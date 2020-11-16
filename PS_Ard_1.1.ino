
/* Programa per a controlar el termo i la piscina a partir de la informació que ve de l'intersor Fronius
   v2 L'arduino fa molt poca feina, tot ho fa la Raspberry. Prova GitHub

   Ordres que accepta:
   - Piscina-ON
     --> retorna Piscina-ACK
   - Piscina-OFF
     --> retorna Piscina-ACK
   - Servo-<graus> (en princpi els graus van de 0 a 180, però la majoria de servos no hi arriben.
     --> retorna Servo-ACK
   - Sal-ON / Sal-OFF
   - Llums-ON / Llums-OFF
   - Hall
     --> retorna Hall-<valor>- (un valor "float" proporcional a la potència per una ona sinusoidal).
   - Ver
     --> retorna Ver-<valor>- (La versió del programa).

   Versió 2.1 Rep ordres via serie i contesta. Accepta Piscina i Servo amb graus.
   Versió 2.2 Igual que 1 però ara ja actuant sobre els dispositius
   Versió 2.3 Inclou sensor d'efecte Hall i comanda per llegir-ho.

   Versió PS_Ard_1.0 Inclou tot l'anterior més comanda versió.
   Versió PS_Ard_1.1 Inclou SAL i LLUMS.

*/

#include <Servo.h>
#include <ArduinoSTL.h>

const int mostra = 400; //Si hi poso 600, l'Arduino peta (té 32K!!)

std::vector<int> vec(mostra);
double promig;
double total;
double ttotal;

Servo servo;
String a;
int grausservo = 0;
int grausservoantic = 0;
int sensorHall = A0;
int sensorValue;


// Arduino pin numbers
const int ControlServo = 9; // Sortida al control del servo
const int RelePiscina = 8; // Sortida al relé de la piscina
const int ReleSal = 7; // Sortida al relé de la piscina
const int ReleLlums = 6; // Sortida al relé de la piscina


void setup() {
  Serial.begin(9600);
  Serial.setTimeout(100);
  pinMode(RelePiscina, OUTPUT);
  digitalWrite(RelePiscina, HIGH); //Relé off
  pinMode(ReleSal, OUTPUT);
  digitalWrite(ReleSal, HIGH); //Relé off
  pinMode(ReleLlums, OUTPUT);
  digitalWrite(ReleLlums, HIGH); //Relé off

  servo.attach(ControlServo);  // Sortida, al servomotor
  servo.write(0);   // Servo a 0 graus
}

void loop() {
  String a;

  if (Serial.available()) {
    String ordre = Serial.readString();

    // Actua piscina ----------------------------------

    if (ordre.substring(0, 8) == "Piscina-") {
      Serial.println("Piscina-ACK");
      if (ordre.substring(8, 11) == "OFF") {
        digitalWrite(RelePiscina, HIGH);
      }
      else {
        digitalWrite(RelePiscina, LOW);
      }
    }

    // Actua sal ----------------------------------

    if (ordre.substring(0, 4) == "Sal-") {
      Serial.println("Sal-ACK");
      if (ordre.substring(4, 7) == "OFF") {
        digitalWrite(ReleSal, HIGH);
      }
      else {
        digitalWrite(ReleSal, LOW);
      }
    }

    // Actua llums ----------------------------------

    if (ordre.substring(0, 6) == "Llums-") {
      Serial.println("Llums-ACK");
      if (ordre.substring(6, 9) == "OFF") {
        digitalWrite(ReleLlums, HIGH);
      }
      else {
        digitalWrite(ReleLlums, LOW);
      }
    }

    // Actua servo ----------------------------------

    if (ordre.substring(0, 6) == "Servo-") {
      Serial.println("Servo-ACK");

      a = ordre.substring(6);
      grausservo = a.toInt();

      if (grausservo > grausservoantic) { // Apugem el potenciòmetre
        for (int i = grausservoantic; i < grausservo; i++) {
          servo.write(i);
          delay (20);  /* smooth mode*/
        }
      }

      if (grausservo < grausservoantic) { // Baixem el potenciòmetre
        for (int i = grausservoantic; i > grausservo; i--) {
          servo.write(i);
          delay (20);  /* smooth mode*/
        }
      }
      grausservoantic = grausservo;
    }

    // Actua Hall (triga com un segon a contestar...) ----------------------------------

    if (ordre.substring(0, 4) == "Hall") {
      ttotal = 0;
      for (int i = 0; i < 5; i++) {

        for (int z = 0; z < mostra; z++) {
          vec[z] = analogRead(A0);
        }

        total = 0;
        for (int z = 0; z < mostra; z++) {
          total = total + vec[z];
        }
        promig = int(total / mostra);

        total = 0;
        for (int z = 0; z < mostra; z++) {
          total = total + abs(vec[z] - promig);
        }
        ttotal = ttotal + total;
        delay(7 + i * 3); // per que sigui més rar i aleatori... Tota una ona de AC són 20 milis.
      }
      Serial.print("Hall-");
      Serial.print(ttotal / 5);
      Serial.println("-");
    }


    // Actua Ver (retorna la versió del programa que està executant l'Arduino (per si no ho recordem...) ----------------------------------

    if (ordre.substring(0, 3) == "Ver") {
      Serial.println("Ver-PS_Ard_1.1-");
    }

  }
}
