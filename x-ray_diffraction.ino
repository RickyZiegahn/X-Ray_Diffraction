//Version 1.0 last updated 20-June-2018
//https://github.com/RickyZiegahn/X-Ray_Diffraction

#define pulse_high 10
#define pulse_rate 5
int detector = 4;
int d_dir = 7; //direction controller of detector motor
int d_loc = 0; //location of detector arm
int sample = 8;
int s_dir = 12; //direction controller of sample motor
int s_loc = 0; //location of sample arm
int pulse_low (pulse_rate - pulse_high); //The sum of the pulse length and lowtime is the length of one full cycle
int steps = 0;
int motor = 0;
int counter = 2; //pulses come into pin 2
int counts = 0;
int len = 1000;
float current_degree = 0;
float starting_degree = 0;
float ending_degree = 0;
float degree_increment = 0;
float factor = 400;
float constant = 0;

float degrees_to_steps(float deg) {
  float temp_step = deg * factor + constant;
  return temp_step;
}

float steps_to_degrees(int steps) {
  float temp_degree = (steps - constant)/factor;
  return temp_degree;
}

void wait_for_input() {
  while(!Serial.available()) {
  }
}

void confirm_flag() {
  Serial.println(999999999);
}

void inc_count() {
  counts += 1; //increments the number of counts detected each time there is a pulse
}

void accept_length() {
  wait_for_input();
  len = Serial.parseInt(); //reads length input
}

void accept_parameters() {
  wait_for_input();
  starting_degree = Serial.parseFloat();
  wait_for_input();
  ending_degree = Serial.parseFloat();
  wait_for_input();
  degree_increment = Serial.parseFloat();
  wait_for_input();
  len = Serial.parseInt();
}

void count() {
  //Serial.println(); //reports zero unless this line is added
  int t1 = millis();
  int t2 = millis();
  int dt = 0;
  while (dt < len) {
    t2 = millis();
    dt = t2 - t1;
  }
  Serial.println(counts);
  dt = 0;
}

void drive(int steps, int motor) {
  choose_direction(steps, motor);
  move_steps(steps, motor);
}  

void choose_direction(int steps, int motor) {
  if(steps > 0){
    if(motor == 1){
      digitalWrite(s_dir, HIGH);  
    }
    if(motor == 2){
      digitalWrite(d_dir, HIGH);
    }
  }
  if(steps < 0){
    if(motor == 1){
      digitalWrite(s_dir, LOW);  
    }
    if(motor == 2){
      digitalWrite(d_dir, LOW);
    }
  }
}

void move_steps(int steps, int motor) {
  if(motor == 1){
    for(int i=1; i <= abs(steps); i++){
      digitalWrite(sample, HIGH);
      delayMicroseconds(pulse_high);
      digitalWrite(sample, LOW);
      delayMicroseconds(pulse_low);
    }
  }
  if(motor == 2){
    for(int i=1; i <= abs(steps); i++){
      digitalWrite(detector, HIGH);
      delayMicroseconds(pulse_high);
      digitalWrite(detector, LOW);
      delayMicroseconds(pulse_low);
    }
  }
}

void accept_drive() {
  wait_for_input();
  motor = Serial.parseInt(); //read motor input
  wait_for_input();
  steps = Serial.parseInt(); //read step input
  drive(steps, motor);
  confirm_flag();
}


void setup() {
  pinMode(detector, OUTPUT);
  pinMode(d_dir, OUTPUT);
  pinMode(sample, OUTPUT);
  pinMode(s_dir, OUTPUT);
  pinMode(counter, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(counter), inc_count, RISING);
  Serial.begin(9600);
}

void loop() {
  wait_for_input();
  int a = Serial.parseInt();
  if(a == 1) {
    accept_drive();
    accept_drive();
    d_loc = 0;
    s_loc = 0;
    wait_for_input();
    int b = Serial.parseInt();
    if (b == 1) {
      accept_parameters();
      //move to starting position
      float fsteps = degrees_to_steps(starting_degree);
      drive(round(fsteps/2), 1);
      s_loc += round(fsteps/2);
      drive(round(fsteps), 2);
      d_loc += round(fsteps);
      counts = 0;
      count();
      
      //proceed to the end
      for (int i; i <= 999999999; i++) { //number is arbitrarily large
        float wanted_degree = starting_degree + degree_increment * i;
        float unrounded_steps = degrees_to_steps(wanted_degree);
        int s_steps = round(unrounded_steps/2) - s_loc;
        int d_steps = round(unrounded_steps) - d_loc;
        drive(s_steps, 1);
        s_loc += s_steps;
        drive(d_steps, 2);
        d_loc += d_steps;
        counts = 0;
        count();
        if (wanted_degree < ending_degree) {
          continue;
        }
        if (wanted_degree >= ending_degree) {
          break;
        }
      }
    }
    else {
      //return to beginning of loop
    }
  }
  if(a == 2) {
    wait_for_input();
    int b = Serial.parseInt();
    if (b == 1) { //drive() function from python
      accept_drive();
    }
    if (b == 2) { //set_location() function from python
    }
    if (b == 3) { //goto() function from python
      accept_drive();
    }
    if (b == 4) { // function from python
      accept_length();
      counts = 0;
      count();
    }
    else {
      //returns to beginning of loop
    }
  }
  else {
  }
}
