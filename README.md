# BP - serverová čast, Web stránka

### Funkcionalita

Prvá vec je vybrať si rolu: Admin, Používateľ. Admin je predpripravený účet, ktorý schvaľuje prístup k schránkam. Užívateľ si môže prihlásiť alebo si vytvoriť účet. Pri vytváraní účtu sa požaduje meno, email a heslo. Po vytvoreni účtu sa uźívateľ dokáže prihlásiť a požíadať si prístup k jemu zvolenej schránke. Výber medzi dvoma. Potom čaká na schválenie alebo zamietnutie. Pri schválení sa ukáže užívateľovi jednorázový kód ku schránke, ostatným užívateľom sa ukáže status schránky ako obsadený. Po zadaní kódu do fyzického hardwaru sa kód z databázy vymaže a schránka sa znova chová ako volná. 

### Web Hosting

Web hosting je urobený cez providera [Render](https://render.com/). 

Stránka sa nachádza na adrese: https://bp-lysa.onrender.com/

### Admin

Admin je predpripravený účet. Do adminu sa prihlási pomoocu emailu a hesla (viď nižšie). Po prihlásení vidí admin dve schránky pri ktorých je napísané, ktorý užívateľ ich má pridelené, ktorý používateľ si o ne zažiadal a aký kód je potrebný na odomknutie schránky. Poslednou časťou tabuľky je stĺpec "akcie" ktorý zodpovedá za spravovanie žiadostí od užívateľov. 

Email: admin@example.com

Heslo: adminpassword

# BP - ESP kód

Kód obsahuje: 
- Pripojenie k WiFi
- Zobrazovanie na OLED displeji
- Čítanie PIN kódu z 4x4 klávesnice
- Overenie kódu cez HTTP request na server
- Odomknutie zámku
- Režim nečinnosti s prebudením cez klávesu `D`

### Hlavný kód (Arduino IDE)

```cpp
#include <Wire.h>
#include <U8g2lib.h>
#include <SPI.h>
#include <Keypad.h>
#include <WiFi.h>
#include <HTTPClient.h>

// === OLED Display (SH1106 SPI) ===
U8G2_SH1106_128X64_NONAME_F_4W_HW_SPI u8g2(
  U8G2_R0, /* CS=*/ 5, /* DC=*/ 16, /* RESET=*/ 17
);

// === WiFi Config ===
const char* ssid       = "It burns when IP";
const char* password   = "7UFpqg74NQpuFNGC";
const char* server_url = "http://192.168.0.252:5000/check_code";

// === Keypad Config ===
const byte ROWS = 4, COLS = 4;
char keys[ROWS][COLS] = {
  {'1','2','3','A'},
  {'4','5','6','B'},
  {'7','8','9','C'},
  {'*','0','#','D'}
};
byte rowPins[ROWS] = {32, 33, 25, 26};
byte colPins[COLS] = {27, 14, 12, 13};
Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

// === Solenoids ===
#define LOCK1_PIN 4
#define LOCK2_PIN 2

// === State ===
String code = "";
unsigned long lastActivity = 0;
const unsigned long IDLE_TIMEOUT = 30UL * 1000UL; // 30 seconds

// Footer at the bottom
void drawFooter() {
  u8g2.setFont(u8g2_font_5x7_tr);
  const char *footer = "#: Confirm  *: Clear";
  int16_t width = u8g2.getStrWidth(footer);
  u8g2.drawStr((128 - width) / 2, 63, footer);
}

void setup() {
  Serial.begin(115200);
  pinMode(LOCK1_PIN, OUTPUT);
  pinMode(LOCK2_PIN, OUTPUT);
  digitalWrite(LOCK1_PIN, LOW);
  digitalWrite(LOCK2_PIN, LOW);

  u8g2.begin();
  u8g2.clearBuffer();
  u8g2.setFont(u8g2_font_ncenB08_tr);

  // Show connecting
  u8g2.drawStr(0, 10, "Connecting to WiFi...");
  u8g2.sendBuffer();

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
  }

  // Connected confirmation
  u8g2.clearBuffer();
  u8g2.drawStr(0, 10, "Connected!");
  u8g2.sendBuffer();
  delay(1000);

  // Initial PIN prompt
  u8g2.clearBuffer();
  u8g2.drawStr(0, 10, "Enter PIN:");
  drawFooter();
  u8g2.sendBuffer();
  lastActivity = millis();
}

void loop() {
  // Sleep-mode check
  if (millis() - lastActivity > IDLE_TIMEOUT) {
    u8g2.clearBuffer();
    u8g2.setFont(u8g2_font_ncenB10_tr);
    u8g2.drawStr(0, 20, "Sleep mode...");
    u8g2.setFont(u8g2_font_ncenB08_tr);
    u8g2.drawStr(0, 40, "Press D to wake up");
    u8g2.sendBuffer();

    // Wait until D pressed
    while (true) {
      char wakeKey = keypad.getKey();
      if (wakeKey == 'D') {
        code = "";
        lastActivity = millis();
        u8g2.clearBuffer();
        u8g2.setFont(u8g2_font_ncenB08_tr);
        u8g2.drawStr(0, 10, "Enter PIN:");
        drawFooter();
        u8g2.sendBuffer();
        break;
      }
      delay(100);
    }
  }

  char key = keypad.getKey();
  if (key) {
    lastActivity = millis();
    if (key == '#') {
      checkCode(code);
      code = "";
    } else if (key == '*') {
      code = "";
      u8g2.clearBuffer();
      u8g2.drawStr(0, 10, "Code cleared");
      u8g2.sendBuffer();
      delay(1000);
      u8g2.clearBuffer();
      u8g2.drawStr(0, 10, "Enter PIN:");
      drawFooter();
      u8g2.sendBuffer();
    } else {
      code += key;
      u8g2.clearBuffer();
      u8g2.drawStr(0, 10, "Enter PIN:");
      u8g2.setCursor(0, 30);
      u8g2.print(code);
      drawFooter();
      u8g2.sendBuffer();
    }
  }
}

void checkCode(const String& enteredCode) {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  http.begin(server_url);
  http.addHeader("Content-Type", "application/json");
  String payload = "{\"code\":\"" + enteredCode + "\"}";
  int httpResponseCode = http.POST(payload);
  u8g2.clearBuffer();

  if (httpResponseCode > 0) {
    String response = http.getString();
    if (response == "locker1" || response == "locker2") {
      int lockPin = (response == "locker1") ? LOCK1_PIN : LOCK2_PIN;
      String lockName = (response == "locker1") ? "Locker 1" : "Locker 2";
      // Opening
      u8g2.drawStr(0, 10, ("Opening " + lockName + "...").c_str());
      u8g2.sendBuffer();
      digitalWrite(lockPin, HIGH);
      delay(10000);
      digitalWrite(lockPin, LOW);
      // Confirmation
      u8g2.clearBuffer();
      u8g2.drawStr(0, 10, (lockName + " opened").c_str());
      u8g2.sendBuffer();
      delay(1000);
    } else {
      u8g2.drawStr(0, 10, "Wrong code.");
      u8g2.sendBuffer();
      delay(1000);
    }
  } else {
    u8g2.drawStr(0, 10, "HTTP error:");
    u8g2.setCursor(0, 30);
    u8g2.print(httpResponseCode);
    u8g2.sendBuffer();
    delay(1000);
  }
  http.end();

  // Back to PIN prompt
  u8g2.clearBuffer();
  u8g2.drawStr(0, 10, "Enter PIN:");
  drawFooter();
  u8g2.sendBuffer();
}