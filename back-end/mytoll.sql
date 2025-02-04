DROP SCHEMA IF EXISTS mydb;
CREATE SCHEMA mydb;
USE mydb;

CREATE TABLE IF NOT EXISTS `mydb`.`Operator` (
  `idOperator` VARCHAR (45)   NOT NULL AUTO_INCREMENT,
  `name` VARCHAR (45) NOT NULL UNIQUE, 
  PRIMARY KEY (`idOperator`));


CREATE TABLE IF NOT EXISTS `mydb`.`Pass` (
  `idPass` VARCHAR (45)  NOT NULL,
  `idToll` VARCHAR (45)   NOT NULL,
  `idTag` VARCHAR (45)   NOT NULL,
  `idOperator` VARCHAR (45)   NOT NULL,
  `Charge` FLOAT NOT NULL,
  `timestamp` TIMESTAMP NOT NULL,
  PRIMARY KEY (`idPass`),
  FOREIGN KEY (`idToll`) REFERENCES `mydb`.`Toll` (`idToll`),
  FOREIGN KEY (`idTag`) REFERENCES `mydb`.`Tag` (`idTag`));



CREATE TABLE IF NOT EXISTS `mydb`.`Settlement` (
  `idSettlement` VARCHAR (45)   NOT NULL,
  `Paying_Operator` VARCHAR (45)   NOT NULL,
  `Paid_Operator` VARCHAR (45)   NOT NULL,
  `timestamp` TIMESTAMP NOT NULL,
  PRIMARY KEY (`idSettlement`),
  FOREIGN KEY (`Paying_Operator`) REFERENCES `mydb`.`Operator` (`idOperator`),
  FOREIGN KEY (`Paid_Operator`) REFERENCES `mydb`.`Operator` (`idOperator`));


CREATE TABLE IF NOT EXISTS `mydb`.`Toll` (
  `idToll` VARCHAR (45)   NOT NULL,
  `idOperator` VARCHAR (45)   NOT NULL,
  `Name` VARCHAR(45) NOT NULL,
  `Locality` VARCHAR(45) NOT NULL,
  `Longitude` INT NOT NULL,
  `Latitude` INT NOT NULL,
  `Email` VARCHAR(45) NULL,
  `PM` VARCHAR(45) NOT NULL,
  `Price_1` DECIMAL NOT NULL,
  `Price_2` DECIMAL NOT NULL,
  `Price_3` DECIMAL NOT NULL,
  `Price_4` DECIMAL NOT NULL,
  `Road` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`idToll`),
  FOREIGN KEY (`idOperator`) REFERENCES `mydb`.`Operator` (`idOperator`));



CREATE TABLE IF NOT EXISTS `mydb`.`User` (
  `idUser` VARCHAR (45)   NOT NULL,
  `Username` VARCHAR(45) NOT NULL,
  `Type` VARCHAR(45) NOT NULL);


CREATE TABLE IF NOT EXISTS `mydb`.`Tag` (
  `idTag` VARCHAR (45)   NOT NULL,
  `idOperator` VARCHAR (45)   NOT NULL,
  `Type` VARCHAR (45)   NOT NULL,
  PRIMARY KEY (`idTag`),
  FOREIGN KEY (`idOperator`) REFERENCES `mydb`.`Operator` (`idOperator`));

SET FOREIGN_KEY_CHECKS = 0;

INSERT INTO Operator (idOperator, name)
SELECT DISTINCT OpID, Operator
FROM tollstations2024;

LOAD DATA INFILE 'C:\Users\IV\Downloads\tollstations2024.csv'
INTO TABLE Toll
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(TollID, OpID, Name, Locality, Longitude, Latitude, Email, PM, Price_1, Price_2, Price_3, Price_4, Road);

INSERT INTO Tag (idTag, idOperator, Type)
SELECT DISTINCT idTag, OpID, 1  -- Assuming '1' as default Type
FROM passes-sample;

LOAD DATA INFILE 'C:\Users\IV\Downloads\passes-sample.csv'
INTO TABLE Pass
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(idPass, idToll, idTag, idOperator, Charge, timestamp);

SET FOREIGN_KEY_CHECKS = 1;

SELECT * FROM Toll LIMIT 10;
SELECT * FROM Pass LIMIT 10;
