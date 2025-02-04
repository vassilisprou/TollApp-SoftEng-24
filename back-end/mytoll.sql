DROP SCHEMA IF EXISTS cooking_show;
DROP USER IF EXISTS 'cook'@'localhost';
DROP USER IF EXISTS 'admin'@'localhost';
CREATE SCHEMA cooking_show;
USE cooking_show;


CREATE TABLE IF NOT EXISTS `mydb`.`Operator` (
  `idOperator` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR (100) NOT NULL UNIQUE, 
  PRIMARY KEY (`idOperator`));


CREATE TABLE IF NOT EXISTS `mydb`.`Pass` (
  `idPass` INT NOT NULL,
  `idToll` INT NOT NULL,
  `idOperator` INT NOT NULL,
  `Charge` DECIMAL NOT NULL,
  `timestamp` TIMESTAMP NOT NULL,
  PRIMARY KEY (`idPass`),
  FOREIGN KEY (`idToll`) REFERENCES `mydb`.`Toll` (`idToll`),
  FOREIGN KEY (`idTag`) REFERENCES `mydb`.`Tag` (`idTag`));



CREATE TABLE IF NOT EXISTS `mydb`.`Settlement` (
  `idSettlement` INT NOT NULL,
  `Paying_Operator` INT NOT NULL,
  `Paid_Operator` INT NOT NULL,
  `timestamp` TIMESTAMP NOT NULL,
  PRIMARY KEY (`idSettlement`),
  FOREIGN KEY (`Paying_Operator`) REFERENCES `mydb`.`Operator` (`idOperator`),
  FOREIGN KEY (`Paid_Operator`) REFERENCES `mydb`.`Operator` (`idOperator`));


CREATE TABLE IF NOT EXISTS `mydb`.`Toll` (
  `idToll` INT NOT NULL,
  `idOperator` INT NOT NULL,
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
  `idUser` INT NOT NULL,
  `Username` VARCHAR(45) NOT NULL,
  `Type` VARCHAR(45) NOT NULL);


CREATE TABLE IF NOT EXISTS `mydb`.`Tag` (
  `idTag` INT NOT NULL,
  `idOperator` INT NOT NULL,
  `Type` INT NOT NULL,
  PRIMARY KEY (`idTag`),
  FOREIGN KEY (`idOperator`) REFERENCES `mydb`.`Operator` (`idOperator`));