DROP DATABASE mydb;
CREATE DATABASE mydb;
USE mydb;

CREATE TABLE mydb . Operator  (
   idOperator  VARCHAR (45)   NOT NULL,
   name  VARCHAR (45) NOT NULL UNIQUE, 
  PRIMARY KEY ( idOperator ));


CREATE TABLE      mydb . Tag  (
   idTag  VARCHAR (45)   NOT NULL,
   idOperator  VARCHAR (45)   NOT NULL,
  PRIMARY KEY ( idTag ),
  FOREIGN KEY ( idOperator ) REFERENCES  mydb . Operator  ( idOperator ));

CREATE TABLE      mydb . Toll(
   idToll  VARCHAR (45)   NOT NULL,
   idOperator  VARCHAR (45)   NOT NULL,
   Name  VARCHAR(100) NOT NULL,
   Locality  VARCHAR(45) NOT NULL,
   Longitude FLOAT NOT NULL,
   Latitude  FLOAT NOT NULL,
   Email  VARCHAR(45) NOT  NULL,
   PM  VARCHAR(45) NOT NULL,
   Price_1  DECIMAL(10,2) NOT NULL,
   Price_2  DECIMAL(10,2) NOT NULL,
   Price_3  DECIMAL(10,2) NOT NULL,
   Price_4  DECIMAL(10,2) NOT NULL,
   Road  VARCHAR(45) NOT NULL,
  PRIMARY KEY ( idToll ),
  FOREIGN KEY ( idOperator ) REFERENCES  mydb . Operator  ( idOperator ));

CREATE TABLE  mydb . Pass  (
  idPass VARCHAR(45) NOT NULL PRIMARY KEY DEFAULT (UUID()),
   idToll  VARCHAR (45)   NOT NULL,
   idTag  VARCHAR (45)   NOT NULL,
   idOperator  VARCHAR (45)   NOT NULL,
   Charge  FLOAT NOT NULL,
   passType VARCHAR(45) ,
   timestamp  TIMESTAMP NOT NULL,
  FOREIGN KEY ( idToll ) REFERENCES  mydb . Toll  ( idToll ) ON DELETE CASCADE
ON UPDATE CASCADE , 
  FOREIGN KEY ( idTag ) REFERENCES  mydb . Tag  ( idTag ));


CREATE TABLE  mydb . Pass  (
  idPass VARCHAR(45) NOT NULL PRIMARY KEY
   idToll  VARCHAR (45)   NOT NULL,
   idTag  VARCHAR (45)   NOT NULL,
   idOperator  VARCHAR (45)   NOT NULL,
   Charge  FLOAT NOT NULL,
   passType VARCHAR(45) ,
   timestamp  TIMESTAMP NOT NULL,
  FOREIGN KEY ( idToll ) REFERENCES  mydb . Toll  ( idToll ) , 
  FOREIGN KEY ( idTag ) REFERENCES  mydb . Tag  ( idTag ));



CREATE TABLE  mydb . Settlement  (
   idSettlement  VARCHAR (45)   NOT NULL,
   Paying_Operator  VARCHAR (45)   NOT NULL,
   Paid_Operator  VARCHAR (45)   NOT NULL,
   timestamp  TIMESTAMP NOT NULL,
  PRIMARY KEY ( idSettlement ),
  FOREIGN KEY ( Paying_Operator ) REFERENCES  mydb . Operator  ( idOperator ),
  FOREIGN KEY ( Paid_Operator ) REFERENCES  mydb . Operator  ( idOperator ));

CREATE TABLE mydb.Users(
	idUser VARCHAR(45) NOT NULL PRIMARY KEY DEFAULT (UUID()),
    Username VARCHAR(45) NOT NULL,
    Password VARCHAR(45) NOT NULL);
    
    
  CREATE TEMPORARY TABLE temp_Operator ( 
    idOperator VARCHAR(45), 
    name VARCHAR(45), 
    dummy1 VARCHAR(255), dummy2 VARCHAR(255), dummy3 VARCHAR(255), 
    dummy4 VARCHAR(255), dummy5 VARCHAR(255), dummy6 VARCHAR(255), 
    dummy7 VARCHAR(255), dummy8 VARCHAR(255), dummy9 VARCHAR(255), 
    dummy10 VARCHAR(255), dummy11 VARCHAR(255), dummy12 VARCHAR(255), 
    dummy13 VARCHAR(255)
);

LOAD DATA INFILE 'C:/Users/iomak/MySQL/MySQL Server 8.0/Uploads/tollstations2024.csv'
INTO TABLE temp_Operator
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(idOperator, name, @dummy,@dummy,@dummy,@dummy,@dummy,@dummy,@dummy,@dummy,@dummy,@dummy,@dummy,@dummy);

INSERT IGNORE INTO mydb.Operator (idOperator, name)
SELECT DISTINCT idOperator, name FROM temp_Operator;

LOAD DATA INFILE 'C:/Users/iomak/MySQL/MySQL Server 8.0/Uploads/tollstations2024.csv'
INTO TABLE mydb.Toll
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(idOperator,@dummy,idToll,Name,PM,Locality,Road,Latitude,Longitude,Email,Price_1, Price_2, Price_3,Price_4);

  CREATE TEMPORARY TABLE temp_tag ( 
    dummy1 VARCHAR(255),
   dummy2 VARCHAR(255),
   idTag VARCHAR(45), idOperator VARCHAR(45), dummy3 VARCHAR(255));

LOAD DATA INFILE 'C:/Users/iomak/MySQL/MySQL Server 8.0/Uploads/passes-sample.csv'
INTO TABLE temp_tag
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(@dummy,@dummy,idTag, idOperator,@dummy);

INSERT IGNORE INTO mydb.Tag (idTag, idOperator)
SELECT DISTINCT idTag, idOperator from temp_tag;



LOAD DATA INFILE 'C:/Users/iomak/MySQL/MySQL Server 8.0/Uploads/passes-sample.csv'
INTO TABLE mydb.Pass
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(timestamp,idToll,idTag,idOperator,Charge);

UPDATE mydb.Pass 
JOIN mydb.Toll ON mydb.Pass.idToll = mydb.Toll.idToll 
SET mydb.Pass.passType =
  CASE 
    WHEN mydb.Pass.idOperator=mydb.Toll.idOperator then 'home'
    ELSE 'visitor'
  END;





