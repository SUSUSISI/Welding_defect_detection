#include <Ethernet.h>
#include <Vector.h>

Vector<int*> dataSet;
int *data;
int pos;
boolean error = false;
void setup() {
  Serial.begin(115200);
}

void loop() {
  char read_data;
  if (Serial.available()){
    read_data = Serial.read();
    if(read_data == '['){
      data = new int[3];
      pos = 0;
      data[0] = 0;
      data[1] = 0;
      data[2] = 0;
      error = false;
    } else if ( read_data >= '0' && read_data <= '9' ) {
      data[pos] = data[pos] * 10 + read_data - '0';
    } else if ( read_data == ',' ) {
      pos++;
    } else if(read_data == ']') {
      if(!error){
        dataSet.push_back(data);
        Serial.print(data[0]);
        Serial.print('/');
        Serial.print(data[1]);
        Serial.print('/');
        Serial.print(data[2]);
        Serial.println();
      }
    } else
      error = true;
      Serial.println("error Data");
  }
  delay(5);
}
