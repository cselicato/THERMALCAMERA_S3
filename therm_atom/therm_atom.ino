#include <M5Unified.h>
#include <PubSubClient.h>
#include <WiFi.h>
#include <SPIFFS.h>
#include <sstream>
#include <vector>
#include <iterator>

WiFiClient espClient;
PubSubClient client(espClient);

const char* ssid        = "carmen";
const char* password    = "password";
const char* mqtt_server = "test.mosquitto.org";
const char* client_name = "AtomS3ThermalCamera";

const char* pixel_fname = "/M5Stack/pixels.txt";
const char* area_fname  = "/M5Stack/area.txt";
const char* settings_fname  = "/M5Stack/cam_settings.txt";

#define MSG_BUFFER_SIZE (1000*4)
char msg[MSG_BUFFER_SIZE];

String current_pix;
String current_area;
String current_settings;

#include "MLX90640_API.h"
#include "MLX90640_I2C_Driver_ATOMS3.h"

const byte MLX90640_address = 0x33; //Default 7-bit unshifted address of the MLX90640
float emissivity = 0.95;
float TA_SHIFT = 8.0;       //Default shift for MLX90640 in open air
uint8_t rate_setting = 2;
byte readout_mode = 0; 

#define COLS   32
#define ROWS   24

float pixels[COLS * ROWS];

// coordinates of the single pixel
int single_pixel[2];
std::vector<std::vector<int>> single_pixels;
std::vector<int> area;
bool reset_pixels = false;
bool reset_area   = false;

byte speed_setting = 2;

#define INTERPOLATED_COLS 32
#define INTERPOLATED_ROWS 32 // perchè sono 32?

paramsMLX90640 mlx90640;

// Temperature ranges
int MINTEMP   = -20;
int min_v     = 24;
int min_cam_v = -40;        // minumum temp the sensor can measure
int MAXTEMP      = 35;
int max_v        = 35;
int max_cam_v    = 300;     // maximum temp the sensor can measure

// Time interval (in ms) between temperature scale readjustments
long time_interval = 5000;

// Color palette
const uint16_t camColors[] = {
    0x480F, 0x400F, 0x400F, 0x400F, 0x4010, 0x3810, 0x3810, 0x3810, 0x3810,
    0x3010, 0x3010, 0x3010, 0x2810, 0x2810, 0x2810, 0x2810, 0x2010, 0x2010,
    0x2010, 0x1810, 0x1810, 0x1811, 0x1811, 0x1011, 0x1011, 0x1011, 0x0811,
    0x0811, 0x0811, 0x0011, 0x0011, 0x0011, 0x0011, 0x0011, 0x0031, 0x0031,
    0x0051, 0x0072, 0x0072, 0x0092, 0x00B2, 0x00B2, 0x00D2, 0x00F2, 0x00F2,
    0x0112, 0x0132, 0x0152, 0x0152, 0x0172, 0x0192, 0x0192, 0x01B2, 0x01D2,
    0x01F3, 0x01F3, 0x0213, 0x0233, 0x0253, 0x0253, 0x0273, 0x0293, 0x02B3,
    0x02D3, 0x02D3, 0x02F3, 0x0313, 0x0333, 0x0333, 0x0353, 0x0373, 0x0394,
    0x03B4, 0x03D4, 0x03D4, 0x03F4, 0x0414, 0x0434, 0x0454, 0x0474, 0x0474,
    0x0494, 0x04B4, 0x04D4, 0x04F4, 0x0514, 0x0534, 0x0534, 0x0554, 0x0554,
    0x0574, 0x0574, 0x0573, 0x0573, 0x0573, 0x0572, 0x0572, 0x0572, 0x0571,
    0x0591, 0x0591, 0x0590, 0x0590, 0x058F, 0x058F, 0x058F, 0x058E, 0x05AE,
    0x05AE, 0x05AD, 0x05AD, 0x05AD, 0x05AC, 0x05AC, 0x05AB, 0x05CB, 0x05CB,
    0x05CA, 0x05CA, 0x05CA, 0x05C9, 0x05C9, 0x05C8, 0x05E8, 0x05E8, 0x05E7,
    0x05E7, 0x05E6, 0x05E6, 0x05E6, 0x05E5, 0x05E5, 0x0604, 0x0604, 0x0604,
    0x0603, 0x0603, 0x0602, 0x0602, 0x0601, 0x0621, 0x0621, 0x0620, 0x0620,
    0x0620, 0x0620, 0x0E20, 0x0E20, 0x0E40, 0x1640, 0x1640, 0x1E40, 0x1E40,
    0x2640, 0x2640, 0x2E40, 0x2E60, 0x3660, 0x3660, 0x3E60, 0x3E60, 0x3E60,
    0x4660, 0x4660, 0x4E60, 0x4E80, 0x5680, 0x5680, 0x5E80, 0x5E80, 0x6680,
    0x6680, 0x6E80, 0x6EA0, 0x76A0, 0x76A0, 0x7EA0, 0x7EA0, 0x86A0, 0x86A0,
    0x8EA0, 0x8EC0, 0x96C0, 0x96C0, 0x9EC0, 0x9EC0, 0xA6C0, 0xAEC0, 0xAEC0,
    0xB6E0, 0xB6E0, 0xBEE0, 0xBEE0, 0xC6E0, 0xC6E0, 0xCEE0, 0xCEE0, 0xD6E0,
    0xD700, 0xDF00, 0xDEE0, 0xDEC0, 0xDEA0, 0xDE80, 0xDE80, 0xE660, 0xE640,
    0xE620, 0xE600, 0xE5E0, 0xE5C0, 0xE5A0, 0xE580, 0xE560, 0xE540, 0xE520,
    0xE500, 0xE4E0, 0xE4C0, 0xE4A0, 0xE480, 0xE460, 0xEC40, 0xEC20, 0xEC00,
    0xEBE0, 0xEBC0, 0xEBA0, 0xEB80, 0xEB60, 0xEB40, 0xEB20, 0xEB00, 0xEAE0,
    0xEAC0, 0xEAA0, 0xEA80, 0xEA60, 0xEA40, 0xF220, 0xF200, 0xF1E0, 0xF1C0,
    0xF1A0, 0xF180, 0xF160, 0xF140, 0xF100, 0xF0E0, 0xF0C0, 0xF0A0, 0xF080,
    0xF060, 0xF040, 0xF020, 0xF800,
};

// Function declarations
float get_point(float *p, uint8_t rows, uint8_t cols, int8_t x, int8_t y);
void set_point(float *p, uint8_t rows, uint8_t cols, int8_t x, int8_t y, float f);
void get_adjacents_2d(float *src, float *dest, uint8_t rows, uint8_t cols, int8_t x, int8_t y);
float cubicInterpolate(float p[], float x);
float bicubicInterpolate(float p[], float x, float y);
void interpolate_image(float *src, uint8_t src_rows, uint8_t src_cols, float *dest, uint8_t dest_rows, uint8_t dest_cols);
void drawpixels(float *p, uint8_t rows, uint8_t cols, uint8_t boxWidth, uint8_t boxHeight, boolean showVal);
void infodisplay(void);
void auto_scale(int max, int min);
void draw_crosshair(int x, int y, int color);

long loopTime, startTime, endTime, fps, lastUpdate;

// defines what to do when a message is recieved 
void callback(char* topic, byte* payload, unsigned int length) {
    Serial.print("Recieved on topic ");
    Serial.print(topic);
    String message="";
    for (int i=0;i<length;i++) {
      message+=(char)payload[i];
    }
    Serial.print("Mqtt command:");
    Serial.println(message);

    if(strcmp(topic, "/singlecameras/camera1/settings") == 0){
        // write camera settings to file (previous one is overwritten)
        File currentSet = SPIFFS.open(settings_fname,"w");
        currentSet.printf(message.c_str());
        currentSet.close();
        client.publish("/singlecameras/camera1/settings/check", "received settings");
        delay(200);

        ESP.restart();
    }

    if(strcmp(topic, "/singlecameras/camera1/info_request") == 0){
        // publish settings, pixels and area
        client.publish("/singlecameras/camera1/pixels/current", current_pix.c_str(), true);
        client.publish("/singlecameras/camera1/area/current", current_area.c_str(), true);
        client.publish("/singlecameras/camera1/settings/current", current_settings.c_str(), true);
        Serial.println("Received request for info, sending:");
        Serial.println(current_settings.c_str());
        Serial.println(current_area.c_str());
        Serial.println(current_pix.c_str());
    }
    

    if(strcmp(topic, "/singlecameras/camera1/pixels/coord") == 0){
        // get x and y coordinate of the desired pixel and add them to single_pixels
        std::vector<int> coord;
        std::stringstream ss = std::stringstream(message.c_str());
        int f;
        for (int i=0; i<2;i++){
            ss >> f;
            single_pixel[i] = f;
            coord.push_back(f);
        }
        // check if values are valid and do stuff only if they are
        if (coord.at(0)>=ROWS || coord.at(1)>=COLS){
            Serial.println("Received coordinates are invalid :(");
        }
        else {        
            single_pixels.push_back(coord);

            // add pixel to file
            File dataFile = SPIFFS.open(pixel_fname,"a");
            if (dataFile) {
                dataFile.printf("%d %d\n", coord.at(0), coord.at(1));
                dataFile.close();
                client.publish("/singlecameras/camera1/pixel_file","success");
            } else {
                client.publish("/singlecameras/camera1/pixel_file","failed");
            }

            std::ostringstream oss;
            for (int i=0; i<single_pixels.size(); i++){
                std::vector<int> pair = single_pixels[i];
                if (pair.size() == 2){
                    oss << pair[0]<<' '<<pair[1];
                }
                else {
                    Serial.println("Found invalid coordinates in single_pixels vector (dimensions !=2) :(");
                }
                if (i!=single_pixels.size()-1){
                    oss << ",";}
            }

            current_pix = oss.str().c_str();
            client.publish("/singlecameras/camera1/pixels/current", current_pix.c_str(), true);
        }
    }

    else if(strcmp(topic, "/singlecameras/camera1/pixels/reset") == 0){
        reset_pixels = true;
    }

    else if(strcmp(topic, "/singlecameras/camera1/area") == 0){  // get information about the area
        // first two numbers are coord. of the lower left point
        // last two are width and height

        // put received info in a temporary container
        int rc[4];
        std::stringstream ss = std::stringstream(message.c_str());
        int f;
        for (int i=0; i<4;i++){
            ss >> f;
            rc[i] = f;
        }
        // check if values are valid
        bool invalid = rc[0]>=ROWS || rc[1]>=COLS || rc[0]+rc[2]>ROWS || rc[1]+rc[3]>COLS;
        if (invalid){ // values are invalid
            Serial.println("Received area is invalid :(");
            Serial.println("If area was defined before, still sending its data");
        }
        else { // values are valid: define new area and do stuff
            area.clear();
            for (int i=0; i<4;i++){
                area.push_back(rc[i]);
            }
            // publish current area as persistent message
            current_area = message;
            client.publish("/singlecameras/camera1/area/current", current_area.c_str(), true);
            // write area to file (previous one must be overwritten)
            File currentArea = SPIFFS.open(area_fname,"w");
            if (currentArea) {
                currentArea.printf("%d\n%d\n%d\n%d\n", area[0], area[1], area[2], area[3]);

                currentArea.close();
                client.publish("/singlecameras/camera1/area_file","success");
            } else {
                client.publish("/singlecameras/camera1/area_file","failed");
            }
        }
    }

    else if(strcmp(topic, "/singlecameras/camera1/area/reset") == 0){
        reset_area = true;
    }
}

// connects or reconnects to MQTT
// connects -> subscribes to topic
// no -> waits 2 seconds
void reconnect(){
    M5.Display.fillScreen(TFT_BLACK);
    M5.Display.setCursor(5, 5);
    M5.Display.printf("Connecting to MQTT...");
    if (client.connect(client_name)) {
    client.subscribe("/singlecameras/camera1/settings");
    client.subscribe("/singlecameras/camera1/info_request");
    client.subscribe("/singlecameras/camera1/area");
    client.subscribe("/singlecameras/camera1/area/reset");
    client.subscribe("/singlecameras/camera1/pixels/coord");
    client.subscribe("/singlecameras/camera1/pixels/reset");

    M5.Display.printf("Connected and subscribed");
    delay(500);

    } 
    else {
    M5.Display.printf("Failed MQTT connection, rc=");
    M5.Display.print(client.state());
    M5.Display.printf(", wait 2 s");
    delay(2000);
    }
}

void setup() {
    Serial.begin(115200);   // Sets the data rate in bits per second (baud) for serial data transmission
    auto cfg = M5.config();
    M5.begin(cfg);
       
    // Initialize I2C for ATOMS3
    Wire.begin(2, 1);  // SDA=2, SCL=1 for Grove port
    // Wire.setClock(450000);
    Wire.setClock(1000000);

    // Wait for serial connection with timeout (2 seconds max)
    unsigned long serialTimeout = millis() + 2000;
    while (!Serial && millis() < serialTimeout) {
        delay(100);
    }
    M5.Display.printf("\nATOMS3 MLX90640 IR Camera\n");
    Serial.println("ATOMS3 MLX90640 IR Camera"); 
    M5.Display.setTextSize(1);



    // start SPIFFS
    if (SPIFFS.begin()) {  // Start SPIFFS, return 1 on success.
        M5.Display.println("SPIFFS begin.");
    } else { // Initialize the SPIFFS
        M5.Display.println("\nSPIFFS format start...");
        SPIFFS.format();    // Formatting SPIFFS.
        M5.Display.println("SPIFFS format finish");
    }

    // Connect to wifi
    M5.Display.print("\nConnecting WiFi...\n");
    WiFi.mode(WIFI_STA);    // option specifies client only
    WiFi.begin(ssid, password);

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        M5.Display.print(".");
    }
    M5.Display.printf("\nConnected!\n");

    // Configure MQTT 
    client.setServer(mqtt_server, 1883);    // default unencrypted MQTT port is 1883
    client.setCallback(callback); 
    client.setBufferSize(256+4*768);
    delay(1000);    // wait 1 s

    reconnect();

    // recover camera settings from file
    File file_set = SPIFFS.open(settings_fname, "r");
    if (!file_set) {   // if no file is found, create one with  defaults
        File file_set = SPIFFS.open(settings_fname,"w");  // Create file object to write information
        file_set.printf("%d\n%.1f\n%.2f\n%d\n", rate_setting, TA_SHIFT, emissivity, readout_mode);
        file_set.close();
        client.publish("/singlecameras/camera1/settings/check", "Creating empty file");

    }
    else { // read file line by line
        Serial.println("Reading settings file...");
        std::vector<String> lines;
        while (file_set.available()) {
            String line = file_set.readStringUntil('\n');
            line.trim();
            if (line.length() > 0) lines.push_back(line);
        }
        file_set.close();

        if (lines.size() >= 4) {
            rate_setting = (uint8_t) lines[0].toInt();
            TA_SHIFT     = lines[1].toFloat();
            emissivity   = lines[2].toFloat();
            readout_mode = lines[3].toInt();
        }
        float rate_hz = pow(2, rate_setting - 1);
        current_settings = "rate: " + String(rate_hz) +
                 " shift: " + String(TA_SHIFT) +
                 " emissivity: " + String(emissivity) +
                 " mode: " + String(readout_mode);
        Serial.println(current_settings);
        client.publish("/singlecameras/camera1/settings/current", current_settings.c_str(), true);        
        client.publish("/singlecameras/camera1/settings/check", "end of parsing setting file");
    }


    // Initialize MLX90640 sensor
    int status;
    uint16_t eeMLX90640[832];
    status = MLX90640_DumpEE(MLX90640_address, eeMLX90640);
    if (status != 0) Serial.println("Failed to load system parameters");

    status = MLX90640_ExtractParameters(eeMLX90640, &mlx90640);
    if (status != 0) Serial.println("Parameter extraction failed");

    // MLX90640_SetRefreshRate(MLX90640_address, 0x02);    // set rate to 2 Hz (0.5 Hz-64 Hz)
    // MLX90640_SetRefreshRate(MLX90640_address, 0x03);    // set rate to 4 Hz

    MLX90640_SetRefreshRate(MLX90640_address, rate_setting);
    Serial.println(rate_setting);
    if (readout_mode == 0){
        MLX90640_SetChessMode(MLX90640_address);
        Serial.println("Setting chess mode");
    }
    else{
        MLX90640_SetInterleavedMode(MLX90640_address);
        Serial.println("Setting interleaved mode");
    }


    // recover pixel coordinates from file
    File file_pixels = SPIFFS.open(pixel_fname, "r");
    if (!file_pixels) {   // if no file is found, create an empty one
        File new_pixels = SPIFFS.open(pixel_fname,"w");  // Create file object to write information
        new_pixels.close();
    }
    else { // read file line by line
        while (file_pixels.available()) {
            String line = file_pixels.readStringUntil('\n');  // Read one line
            line.trim(); // Remove trailing newline or spaces
            if (line.length() == 0) continue;
            // add read pixels to vector
            int ind = line.indexOf(' ');
            if (ind == -1) continue; // Skip invalid lines

            String xStr = line.substring(0, ind);
            String yStr = line.substring(ind + 1);

            int x = xStr.toInt();
            int y = yStr.toInt();

            // Add to pixel vector
            single_pixels.push_back({x, y});
        }
    }

    if (single_pixels.size()!=0){
        std::ostringstream oss;
        for (int i=0; i<single_pixels.size(); i++){
            std::vector<int> pair = single_pixels[i];
            if (pair.size() == 2){
                oss << pair[0]<<' '<<pair[1];
            }
            else {
                Serial.println("Found invalid coordinates in single_pixels vector (dimensions !=2) :(");
            }
            if (i!=single_pixels.size()-1){
                oss << ",";}
        }

        current_pix = oss.str().c_str();
    }
    else {
        current_pix = "none";
    }
    // recover area from file
    File file_area = SPIFFS.open(area_fname, "r");
    if (!file_area) {   // if no file is found, create an empty one
        File new_area = SPIFFS.open(area_fname,"w");  // Create file object to write information
        new_area.close();
    }
    else { // read file line by line
        while (file_area.available()) {
            String line = file_area.readStringUntil('\n');
            line.trim();
            area.push_back(line.toInt());
        }
    }
    if (area.size()!=0){
    std::ostringstream a_oss;
    for (int i=0; i<area.size(); i++){
        if (i==area.size()-1){
            a_oss << area[i];
        }
        else{
            a_oss << area[i]<<' ';
        }
    }
    current_area = a_oss.str().c_str();
    }
    else {
        current_area = "none";
    }
    // Setup display to show image and info
    M5.Display.fillScreen(TFT_BLACK);
    infodisplay();
}

void loop() {
    M5.update();
    if (!client.connected()) {
        reconnect();
    }
    client.loop();

    loopTime = millis();
    startTime = loopTime;
    
    client.publish("/singlecameras/camera1/pixels/connected", "1");

    // Long press button for power off (hold for 3 seconds)
    if (M5.BtnA.pressedFor(3000)) {
        M5.Display.fillScreen(TFT_BLACK);
        M5.Display.setTextColor(YELLOW, BLACK);
        M5.Display.drawCentreString("Power Off...", 64, 40, 2);
        delay(1000);
        esp_deep_sleep_start();
    }

    if (reset_pixels){
        reset_pixels = false;
        // when a reset mesage arrives, delete previous pixel coord.
        single_pixels.clear();
        File emptyFile = SPIFFS.open(pixel_fname,"w");  // Create aFile object to write information
        emptyFile.close();  // Close the file when writing is complete.
        current_pix = "none";
        client.publish("/singlecameras/camera1/pixels/current", current_pix.c_str(), true);
    }

    if (reset_area){
        reset_area = false;
        area.clear();
        File emptyFile = SPIFFS.open(area_fname,"w");  // Create aFile object to write information
        emptyFile.close();  // Close the file when writing is complete.
        current_area = "none";
        client.publish("/singlecameras/camera1/area/current", current_area.c_str(), true);
    }
    
    // Read thermal data
    for (byte x = 0; x < speed_setting; x++) {
        uint16_t mlx90640Frame[834];
        int status = MLX90640_GetFrameData(MLX90640_address, mlx90640Frame);
        if (status < 0) {
            Serial.print("GetFrame Error: ");
            Serial.println(status);
        }

        float vdd = MLX90640_GetVdd(mlx90640Frame, &mlx90640);
        float Ta = MLX90640_GetTa(mlx90640Frame, &mlx90640);
        float tr = Ta - TA_SHIFT;   //Reflected temperature based on the sensor ambient temperature
        MLX90640_CalculateTo(mlx90640Frame, &mlx90640, emissivity, tr, pixels);
        
        int mode_ = MLX90640_GetCurMode(MLX90640_address);
        MLX90640_BadPixelsCorrection((&mlx90640)->brokenPixels, pixels, mode_, &mlx90640);
    }

    // Process thermal image
    float dest_2d[INTERPOLATED_ROWS * INTERPOLATED_COLS];
    interpolate_image(pixels, ROWS, COLS, dest_2d, INTERPOLATED_ROWS, INTERPOLATED_COLS);

    // Adjust for left-side thermal image (96 pixels wide, full height)
    uint16_t boxWidth = 96 / INTERPOLATED_COLS;  // About 3 pixels per thermal pixel
    uint16_t boxHeight = 128 / INTERPOLATED_ROWS;  // Full height divided by rows
    
    drawpixels(dest_2d, INTERPOLATED_ROWS, INTERPOLATED_COLS, boxWidth, boxHeight, false);
    
    // Calculate min/max/avg temperatures
    max_v = -999;  // Start with very low value
    min_v = 999;   // Start with very high value
    float avg_v = 0;
    int valid_pixels = 0;
    int spot_v = pixels[384];  // Center pixel (768/2 = 384) not used
    
    // Use COLS * ROWS for actual pixel count
    for (int itemp = 0; itemp < COLS * ROWS; itemp++) {
        if (pixels[itemp] > max_v) {
            max_v = pixels[itemp];
        }
        if (pixels[itemp] < min_v) {
            min_v = pixels[itemp];
        }
        avg_v += pixels[itemp];
        valid_pixels++;
    }
    if (valid_pixels > 0) {
        avg_v = avg_v / valid_pixels;
    }

    // Clear right side for temperature info
    M5.Display.fillRect(96, 0, 32, 128, TFT_BLACK);
    
    // Display temperature info on the right side
    M5.Display.setTextSize(1);
    M5.Display.setTextColor(TFT_WHITE);

    if (max_v > max_cam_v || max_v < min_cam_v) {
        // If the temperature is above/below the maximum/minimum that can be measured,
        // print error message
        M5.Display.setCursor(98, 10);
        M5.Display.setTextColor(TFT_RED);
        M5.Display.print("Error");
    } else { // Print max, min and average temperature on display
        // Max temperature
        M5.Display.setCursor(98, 20);
        M5.Display.setTextColor(TFT_RED);
        M5.Display.print("Max:");
        M5.Display.setCursor(98, 30);
        M5.Display.print(max_v);
        
        // Min temperature
        M5.Display.setCursor(98, 50);
        M5.Display.setTextColor(TFT_CYAN);
        M5.Display.print("Min:");
        M5.Display.setCursor(98, 60);
        M5.Display.print(min_v);
        
        // Average temperature
        M5.Display.setCursor(98, 80);
        M5.Display.setTextColor(TFT_GREEN);
        M5.Display.print("Avg:");
        M5.Display.setCursor(98, 90);
        M5.Display.printf("%.1fC", avg_v);
        
        // Draw crosshair at center of thermal image
        draw_crosshair(48, 64, TFT_WHITE);

        // Draw crosshair at single pixel
        draw_crosshair(single_pixel[0]*4, single_pixel[1]*4, TFT_BLACK);
        M5.Display.setCursor(98, 5);
        M5.Display.setTextColor(TFT_WHITE);
        M5.Display.printf("%d-%d", MINTEMP, MAXTEMP); // update max/min temperature info shown on display
    }

    loopTime = millis();
    endTime = loopTime;
    fps = 1000 / (endTime - startTime);

    // Update the temperature scale every 5 seconds
    if (loopTime-lastUpdate>time_interval){
        lastUpdate = loopTime;
        auto_scale(max_v, min_v);
    }
    
    // Show FPS and current mode on right side
    M5.Display.setCursor(98, 110);
    M5.Display.setTextColor(TFT_WHITE);
    M5.Display.printf("fps:%d", (int)fps);
    
    // MQTT publishing
    client.connect(client_name);
    bool r = client.publish("/singlecameras/camera1/image", (byte *) pixels, 4*768); 
    client.publish("/singlecameras/camera1/check", r?"ok":"ko");
    String jsonPayload = String("{\"tmax\":") + String(max_v) + ",\"tmin\":" + String(min_v) + ",\"tavg\":" + String(avg_v) + "}";
    client.publish("/singlecameras/camera1/temps", jsonPayload.c_str());
    // if at least one pixel is defined, publish pixel data
    if (single_pixels.size()>0){
        client.publish("/singlecameras/camera1/pixels/data", pixel_data(single_pixels,pixels).c_str());
    }
    // if area is defined, publish its data
    if(area.size() == 4){    // if area is not defined there is nothing to publish
        client.publish("/singlecameras/camera1/area/data", area_data(area,pixels).c_str());
    }

}

String pixel_data(std::vector<std::vector<int>> positions, float values[COLS * ROWS]){
    String out_msg;

    // IMPORTANT: x and y must be swapped to access correct pixel

    // loop on positions
    for(int i=0; i<positions.size(); i++){
        std::vector<int> pos = positions[i];
        if (pos[1]>COLS || pos[0]>ROWS) {
            Serial.println("Found invalid coordinates for pixel");
            out_msg = "Failed on "+ String(pos[0]) + " " + String(pos[1]);
        }

        else {
            float val = values[COLS*pos[0] + pos[1]];
            out_msg = out_msg + String(pos[0]) + " " + String(pos[1]) + " " + String(val);
            if (i < positions.size()-1){
                out_msg = out_msg + ",";
            }
        }
    }

    return out_msg;
}

String area_data(std::vector<int> a, float values[COLS * ROWS]){
    String out_msg;
    int y = a[0];
    int x = a[1];
    int h = a[2];
    int w = a[3];
    // add data of the interesting area to a vector
    std::vector<float> temps;
    if (a[1]>COLS || a[0]>ROWS) {   // TODO: make sure width and height are consistent
        Serial.println("Found invalid coordinates for area");
        String out_msg = "Failed on "+ String(a[0]) + " " + String(a[1]);
    }
    else {
        for(int i=x; i<x+w;i++){
            for(int j=y; j<y+h;j++){
                temps.push_back(values[j*COLS + i]);
            }
        }
        float max = *std::max_element(temps.begin(), temps.end());
        float min = *std::min_element(temps.begin(), temps.end());
        float avg = 0.;
        for(float f : temps){
            avg += f;
        }
        avg = avg/temps.size();
        x = a[0];
        y = a[1];
        w = a[2];
        h = a[3];
        out_msg = "max: "+String(max)+" min: "+String(min)+" avg: "+String(avg)+" x: "+String(x)+" y: "+String(y)+" w: "+String(w)+" h: "+String(h);
    }

    return out_msg;
}
void infodisplay(void) {
    // Clear and update temperature range display on right side
    M5.Display.fillRect(96, 0, 32, 15, TFT_BLACK);  // Clear top area
    M5.Display.setTextColor(TFT_WHITE);
    M5.Display.setTextSize(1);
}

void drawpixels(float *p, uint8_t rows, uint8_t cols, uint8_t boxWidth, uint8_t boxHeight, boolean showVal) {
    int colorTemp;
    for (int y = 0; y < rows; y++) {
        for (int x = 0; x < cols; x++) {
            float val = get_point(p, rows, cols, x, y);

            if (val >= MAXTEMP)
                colorTemp = MAXTEMP;
            else if (val <= MINTEMP)
                colorTemp = MINTEMP;
            else
                colorTemp = val;

            uint8_t colorIndex = map(colorTemp, MINTEMP, MAXTEMP, 0, 255);
            colorIndex = constrain(colorIndex, 0, 255);
            
            M5.Display.fillRect(boxWidth * y, boxHeight * x, boxWidth, boxHeight, camColors[colorIndex]);
        }
    }
}

// Set the maximum and minimum for the temperature color scale as
// the min/max measured minus/plus 10% of their difference
void auto_scale(int max, int min){
    MAXTEMP = max + (max - min)*0.1;
    MINTEMP = min - (max - min)*0.1;
}

// Draw crosshair at the specified position
void draw_crosshair(int x, int y, int color){
    M5.Display.drawCircle(x, y, 3, color);  // Center of 96px wide image
    M5.Display.drawLine(x, y-6, x, y+6, color);  // vertical line
    M5.Display.drawLine(x-6, y, x+6, y, color);  // horizontal line
}

// Interpolation functions
float get_point(float *p, uint8_t rows, uint8_t cols, int8_t x, int8_t y) {
    if (x < 0) x = 0;
    if (y < 0) y = 0;
    if (x >= cols) x = cols - 1;
    if (y >= rows) y = rows - 1;
    return p[y * cols + x];
}

void set_point(float *p, uint8_t rows, uint8_t cols, int8_t x, int8_t y, float f) {
    if ((x < 0) || (x >= cols)) return;
    if ((y < 0) || (y >= rows)) return;
    p[y * cols + x] = f;
}

void interpolate_image(float *src, uint8_t src_rows, uint8_t src_cols, float *dest, uint8_t dest_rows, uint8_t dest_cols) {
    float mu_x = (src_cols - 1.0) / (dest_cols - 1.0);
    float mu_y = (src_rows - 1.0) / (dest_rows - 1.0);

    float adj_2d[16];

    for (uint8_t y_idx = 0; y_idx < dest_rows; y_idx++) {
        for (uint8_t x_idx = 0; x_idx < dest_cols; x_idx++) {
            float x = x_idx * mu_x;
            float y = y_idx * mu_y;
            get_adjacents_2d(src, adj_2d, src_rows, src_cols, x, y);
            float frac_x = x - (int)x;
            float frac_y = y - (int)y;
            float out = bicubicInterpolate(adj_2d, frac_x, frac_y);
            set_point(dest, dest_rows, dest_cols, x_idx, y_idx, out);
        }
    }
}

float cubicInterpolate(float p[], float x) {
    float r = p[1] + (0.5 * x * (p[2] - p[0] + x * (2.0 * p[0] - 5.0 * p[1] + 4.0 * p[2] - p[3] + x * (3.0 * (p[1] - p[2]) + p[3] - p[0]))));
    return r;
}

float bicubicInterpolate(float p[], float x, float y) {
    float arr[4] = {0, 0, 0, 0};
    arr[0] = cubicInterpolate(p + 0, x);
    arr[1] = cubicInterpolate(p + 4, x);
    arr[2] = cubicInterpolate(p + 8, x);
    arr[3] = cubicInterpolate(p + 12, x);
    return cubicInterpolate(arr, y);
}

void get_adjacents_2d(float *src, float *dest, uint8_t rows, uint8_t cols, int8_t x, int8_t y) {
    for (int8_t delta_y = -1; delta_y < 3; delta_y++) {
        float *row = dest + 4 * (delta_y + 1);
        for (int8_t delta_x = -1; delta_x < 3; delta_x++) {
            row[delta_x + 1] = get_point(src, rows, cols, x + delta_x, y + delta_y);
        }
    }
}
