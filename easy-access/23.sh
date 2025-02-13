python cli.py logout
python cli.py login --username admin --passw freepasses4all
python cli.py healthcheck
python cli.py resetpasses
python cli.py healthcheck
python cli.py resetstations
python cli.py healthcheck
python cli.py addpasses --file "C:\Users\iomak\softeng\passes23.csv"
python cli.py healthcheck
python cli.py tollstationpasses --station AM08 --from 20220713 --to 20220727 --format json
python cli.py tollstationpasses --station NAO04 --from 20220713 --to 20220727 --format csv
python cli.py tollstationpasses --station NO01 --from 20220713 --to 20220727 --format csv
python cli.py tollstationpasses --station OO03 --from 20220713 --to 20220727 --format csv
python cli.py tollstationpasses --station XXX --from 20220713 --to 20220727 --format csv
python cli.py tollstationpasses --station OO03 --from 20220713 --to 20220727 --format YYY
python cli.py errorparam --station OO03 --from 20220713 --to 20220727 --format csv
python cli.py tollstationpasses --station AM08 --from 20220714 --to 20220725 --format json
python cli.py tollstationpasses --station NAO04 --from 20220714 --to 20220725 --format csv
python cli.py tollstationpasses --station NO01 --from 20220714 --to 20220725 --format csv
python cli.py tollstationpasses --station OO03 --from 20220714 --to 20220725 --format csv
python cli.py tollstationpasses --station XXX --from 20220714 --to 20220725 --format csv
python cli.py tollstationpasses --station OO03 --from 20220714 --to 20220725 --format YYY
python cli.py passanalysis --stationop AM --tagop NAO --from 20220713 --to 20220727 --format json
python cli.py passanalysis --stationop NAO --tagop AM --from 20220713 --to 20220727 --format csv
python cli.py passanalysis --stationop NO --tagop OO --from 20220713 --to 20220727 --format csv
python cli.py passanalysis --stationop OO --tagop KO --from 20220713 --to 20220727 --format csv
python cli.py passanalysis --stationop XXX --tagop KO --from 20220713 --to 20220727 --format csv
python cli.py passanalysis --stationop AM --tagop NAO --from 20220714 --to 20220725 --format json
python cli.py passanalysis --stationop NAO --tagop AM --from 20220714 --to 20220725 --format csv
python cli.py passanalysis --stationop NO --tagop OO --from 20220714 --to 20220725 --format csv
python cli.py passanalysis --stationop OO --tagop KO --from 20220714 --to 20220725 --format csv
python cli.py passanalysis --stationop XXX --tagop KO --from 20220714 --to 20220725 --format csv
python cli.py passescost --stationop AM --tagop NAO --from 20220713 --to 20220727 --format json
python cli.py passescost --stationop NAO --tagop AM --from 20220713 --to 20220727 --format csv
python cli.py passescost --stationop NO --tagop OO --from 20220713 --to 20220727 --format csv
python cli.py passescost --stationop OO --tagop KO --from 20220713 --to 20220727 --format csv
python cli.py passescost --stationop XXX --tagop KO --from 20220713 --to 20220727 --format csv
python cli.py passescost --stationop AM --tagop NAO --from 20220714 --to 20220725 --format json
python cli.py passescost --stationop NAO --tagop AM --from 20220714 --to 20220725 --format csv
python cli.py passescost --stationop NO --tagop OO --from 20220714 --to 20220725 --format csv
python cli.py passescost --stationop OO --tagop KO --from 20220714 --to 20220725 --format csv
python cli.py passescost --stationop XXX --tagop KO --from 20220714 --to 20220725 --format csv
python cli.py chargesby --opid NAO --from 20220713 --to 20220727 --format json
python cli.py chargesby --opid GE --from 20220713 --to 20220727 --format csv
python cli.py chargesby --opid OO --from 20220713 --to 20220727 --format csv
python cli.py chargesby --opid KO --from 20220713 --to 20220727 --format csv
python cli.py chargesby --opid NO --from 20220713 --to 20220727 --format csv
python cli.py chargesby --opid NAO --from 20220714 --to 20220725 --format json
python cli.py chargesby --opid GE --from 20220714 --to 20220725 --format csv
python cli.py chargesby --opid OO --from 20220714 --to 20220725 --format csv
python cli.py chargesby --opid KO --from 20220714 --to 20220725 --format csv
python cli.py chargesby --opid NO --from 20220714 --to 20220725 --format csv