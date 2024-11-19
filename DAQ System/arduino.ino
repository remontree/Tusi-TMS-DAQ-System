// 캘리브레이션을 위한 데이터 정의
#define NUM_CAL_POINTS 2  // 캘리브레이션 포인트 수
float knownWeights[NUM_CAL_POINTS] = {1.48, 2.16};  // 캘리브레이션 무게 (kg)
long sensorValues[NUM_CAL_POINTS];  // 각 무게에 대한 센서 출력 값

#include <EEPROM.h>
#include <SPI.h>
#include <SD.h>
#include <math.h>

#define CLK 13        // Connect CLK Pin of HX711 to 13th pin of Arduino
#define DOUT 7        // Changed to a pin available on Uno

#define SLOPE_ADDR 0 // EEPROM의 첫 번째 위치(0)에 기울기 저장
#define OFFSET_ADDR sizeof(float) // EEPROM의 다섯 번째 위치(4)에 오프셋 저장

// SD 카드 칩 선택 핀
const int SD_CS_PIN = 4;

unsigned long curTime = 0;
String fileName;
long currentOffset;

byte PD_SCK;      
byte gain = 128;  
byte GAIN;
long OFFSET = 0;  
float SCALE = 1;  

double prevThrust = 0;

float calibrationSlope = 0; // 캘리브레이션 기울기
float calibrationOffset = 0; // 캘리브레이션 오프셋

// function declaration
void set_gain(byte gain);
void set_scale(float scale);
void resetScale(byte numObs);
void set_offset(long offset);
float get_units(byte numObs);
double get_value(byte numObs);
long read_average(byte numObs); 
bool is_ready();
long read(); 

// EEPROM에서 float 값 읽기
float EEPROM_readFloat(int addr) {
  float value;
  EEPROM.get(addr, value);
  return value;
}

// EEPROM에 float 값 쓰기
void EEPROM_writeFloat(int addr, float value) {
  EEPROM.put(addr, value);
}

void setup() {
  int count = 0;
  Serial.begin(9600);

  PD_SCK = CLK;

  pinMode(PD_SCK, OUTPUT);
  pinMode(DOUT, INPUT);

  set_gain(gain);
  
  /*
  // Check SD card connection
  Serial.println("Initializing SD card...");
  if (!SD.begin(SD_CS_PIN)) {
    Serial.println("Card failed, or not present");
  } else {     
    Serial.println("Card initialized.");
  }
  
  // File naming
  while(1) {
    fileName = "test" + String(count) + ".txt";
    File checkFile = SD.open(fileName);
    if(checkFile) {
      Serial.println(count);
      Serial.println("File present");
      checkFile.close();
      count++;
    } else {
      fileName = "test" + String(count) + ".txt";
      break;
    }
  }
  */
  
  // HX711 setup
  delay(500);
  Serial.println("HX711 scale TEST");
  currentOffset = 0;

  // 캘리브레이션 여부 선택
  char temp;
  Serial.println("Press Y to start calibrate or N to use existing calibration");
  while (temp != 'Y' && temp != 'N') {
    if (Serial.available()) {
      temp = Serial.read();
    }
  }

  if (temp == 'Y') {
    multiPointCalibration();  // 다중 포인트 캘리브레이션 수행
  } else {
    // EEPROM에서 캘리브레이션 데이터 읽기
    calibrationSlope = EEPROM_readFloat(SLOPE_ADDR);
    calibrationOffset = EEPROM_readFloat(OFFSET_ADDR);
    Serial.print("Loaded calibration slope: ");
    Serial.println(calibrationSlope);
    Serial.print("Loaded calibration offset: ");
    Serial.println(calibrationOffset);
  }

  Serial.println("Calibration setup complete.");
  Serial.println("Press S to start measuring");
  while (temp != 'S') {
    if (Serial.available()) {
      temp = Serial.read();
    }
  }
  Serial.println("Start measuring");
}

int cnt = 1;

void loop() {
  curTime = millis();
  Serial.println("Current time: " + String(curTime));

  // SD 카드 비활성화 (로드셀 사용 전)
  // digitalWrite(SD_CS_PIN, HIGH);
  long rawValue = read_average(1);
  float weight = getCalibratedWeight(rawValue);
  
  weight *= 9.80665;

  // Pressure data input
  long pressureInput = analogRead(A0);

  double pressure = (double(100) / 490) * (pressureInput - 123);  // Adjusted for 10-bit resolution (UNO)

  // Data naming
  String dataString = String(curTime / 1000.0) + ": " + String(weight) + "[N]" + " & " + String(pressure) + "[bar]" + "(" + String(pressureInput) + ")";

  Serial.println(dataString);
  
  /*
  // SD 카드 활성화 (데이터 기록 전)
  // digitalWrite(SD_CS_PIN, LOW);
  // SD card file open
  File dataFile = SD.open(fileName, FILE_WRITE);
  
  if (dataFile) {
    dataFile.println(dataString);
    dataFile.close();
  } else {
    Serial.println("Error opening datalog.txt");
  }
  // SD 카드 비활성화 (기록 후)
  digitalWrite(SD_CS_PIN, HIGH);
  SD.end();
  */
}

// 다중 점 캘리브레이션 결과 
void multiPointCalibration() {
  Serial.println("Multi-point calibration started");
  for (int i = 0; i < NUM_CAL_POINTS; i++) {
    Serial.print("Place weight in 10 seconds: ");
    Serial.print(knownWeights[i]);
    Serial.println("kg");
    delay(10000);  // 무게를 놓을 시간을 줍니다.

    sensorValues[i] = read_average(10);  // 센서 값을 여러 번 읽어 평균을 구합니다.
    Serial.print("Recorded value: ");
    Serial.println(sensorValues[i]);
  }
  Serial.println("Multi-point calibration completed");

  // 기울기와 오프셋 계산
  calibrationSlope = (knownWeights[1] - knownWeights[0]) / (sensorValues[1] - sensorValues[0]);
  calibrationOffset = knownWeights[0] - calibrationSlope * sensorValues[0];

  // EEPROM에 기울기와 오프셋 저장
  EEPROM_writeFloat(SLOPE_ADDR, calibrationSlope);
  EEPROM_writeFloat(OFFSET_ADDR, calibrationOffset);

  Serial.print("Stored calibration slope: ");
  Serial.println(calibrationSlope);
  Serial.print("Stored calibration offset: ");
  Serial.println(calibrationOffset);
}

float getCalibratedWeight(long sensorValue) {
  return calibrationSlope * sensorValue + calibrationOffset;
}

// HX711 library functions
void set_gain(byte gain) {
  switch (gain) {
    case 128:
      GAIN = 1;
      break;
    case 64:
      GAIN = 3;
      break;
    case 32:
      GAIN = 2;
      break;
  }

  digitalWrite(PD_SCK, LOW);
  read();
}

void set_scale(float scale) {
  SCALE = scale;
}

void resetScale(byte numObs) {
  double sum = read_average(numObs);
  set_offset(sum);
}

void set_offset(long offset) {
  OFFSET = offset;
}

float get_units(byte numObs) {
  return get_value(numObs) / SCALE;
}

double get_value(byte numObs) {
  return read_average(numObs) - OFFSET;
}

long read_average(byte numObs) {
  long sum = 0;
  for (byte i = 0; i < numObs; i++) {
    sum += read();
    yield();
  }
  return sum / numObs;
}

bool is_ready() {
  return digitalRead(DOUT) == LOW;
}

long read() {
  while (!is_ready()) {
    yield();
  }

  unsigned long value = 0;
  uint8_t data[3] = { 0 };
  uint8_t filler = 0x00;

  data[2] = shiftIn(DOUT, PD_SCK, MSBFIRST);
  data[1] = shiftIn(DOUT, PD_SCK, MSBFIRST);
  data[0] = shiftIn(DOUT, PD_SCK, MSBFIRST);

  for (unsigned int i = 0; i < GAIN; i++) {
    digitalWrite(PD_SCK, HIGH);
    digitalWrite(PD_SCK, LOW);
  }

  if (data[2] & 0x80) {
    filler = 0xFF;
  } else {
    filler = 0x00;
  }

  value = ( static_cast<unsigned long>(filler) << 24
      | static_cast<unsigned long>(data[2]) << 16
      | static_cast<unsigned long>(data[1]) << 8
      | static_cast<unsigned long>(data[0]) );

  return static_cast<long>(value);
}
