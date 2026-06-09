# EC200Test

<img width="1084" height="1342" alt="4311963b646e0af85c218b4096527595" src="https://github.com/user-attachments/assets/f2d46108-deef-428e-8cd6-06e1b44f0be0" />

## ECtestWin.py

python -m PyInstaller --onefile ECtestWin.py 

<img width="2004" height="1264" alt="image" src="https://github.com/user-attachments/assets/4efc1ff4-4df4-4cd7-922d-e1da487db988" />



```
python .\ECtest.py
发现串口: COM29 - 描述: Quectel USB AT Port (COM29)
--> 成功匹配到 EC200A AT 端口: COM29

已成功建立连接 COM29，开始测试...
========================================

[执行命令] ---> AT
[模块回应] :
AT
OK

[执行命令] ---> AT+QGMR
[模块回应] :
AT+QGMR
EC200ACNLBR01A13M16

OK

[执行命令] ---> AT+QICSGP=1
[模块回应] :
AT+QICSGP=1
+QICSGP: 1,"UNINET","","",1

OK

[执行命令] ---> AT+CFUN?
[模块回应] :
AT+CFUN?
+CFUN: 1

OK

[执行命令] ---> AT+CPIN?
[模块回应] :
AT+CPIN?
+CPIN: READY

OK

[执行命令] ---> AT+QENG="SERVINGCELL"
[模块回应] :
AT+QENG="SERVINGCELL"
+QENG: "servingcell","LIMSRV","LTE","TDD",460,00,2C17802,407,40936,41,5,5,2495,-97,-10,-67,15,26

OK

[执行命令] ---> AT+QCFG="band"
[模块回应] :
AT+QCFG="band"
+QCFG: "band",0xd0,0x1e200000095

OK

[执行命令] ---> AT+QCFG="nwscanmode"
[模块回应] :
AT+QCFG="nwscanmode"
+QCFG: "nwscanmode",0

OK

========================================
所有测试命令执行完毕，串口已安全关闭。
```

## ECtest.py

<img width="1854" height="1896" alt="image" src="https://github.com/user-attachments/assets/82e92c9a-1495-4e74-b973-6f99565b62b5" />



```
AT+QGMR

EC200ACNLBR01A13M16
OK
AT+QICSGP=1

+QICSGP: 1,"UNINET","","",1
OK
AT+CFUN?

+CFUN: 1
OK
AT+CPIN?

+CPIN: READY
OK
AT+QENG="SERVINGCELL"

+QENG: "servingcell","LIMSRV","LTE","TDD",460,00,2C17803,405,40936,41,5,5,2495,-104,-12,-72,4,20
OK
AT+QCFG="band"

+QCFG: "band",0xd0,0x1e200000095
OK
AT+QCFG="nwscanmode"

+QCFG: "nwscanmode",0
OK
```

<img width="2706" height="1946" alt="image" src="https://github.com/user-attachments/assets/372149dd-42aa-479a-b496-afe5fe891130" />




