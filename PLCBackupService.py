import socket
#import time
import datetime
#import select
#from io import BytesIO
#from io import StringIO
#from StringIO import StringIO
#import ftplib
import os
#import subprocess
import logging
import sys
import traceback


import win32serviceutil
import win32service
import win32event
import servicemanager

#from datetime import datetime, timedelta

#import dbConnector
#import const
#import util


class PLCBackupService(win32serviceutil.ServiceFramework):
    _svc_name_ = "PLCBackupService"
    _svc_display_name_ = "PLC Automated Backup Service"
    _svc_description_ = "Automated backup service for Mitsubishi PLCs"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.is_running = False
        
        # Setup logging for the service
        self.setup_logging()

    def setup_logging(self):
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        current_dateTime = datetime.datetime.now()
        updateTime = current_dateTime.strftime("%Y-%m-%d_%H%M%S")
        log_file = os.path.join(log_dir, f'{updateTime}_service.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            filename=log_file,
            filemode='a'
        )
        self.logger = logging.getLogger('PLCBackupService')

    def SvcStop(self):
        self.logger.info('Service stop signal received')
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.is_running = False

    def SvcDoRun(self):
        self.logger.info('Service starting')
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        self.is_running = True
        self.main()

    def main(self):
        self.logger.info('Service main loop starting')
        
        # Add your virtual environment site-packages to sys.path
        # Replace with your actual virtual environment path
        venv_path = r"E:\pythonProjects\automatedBackups\.venv"
        venv_site_packages = os.path.join(venv_path, "Lib", "site-packages")
        if os.path.exists(venv_site_packages) and venv_site_packages not in sys.path:
            sys.path.append(venv_site_packages)
            self.logger.info(f"Added virtual environment to path: {venv_site_packages}")
        
        # Run the main backup loop
        try:
            import dbConnector
            import const
            import util
            from automatedBackup import backupProcess, log_info, startup
            #from automatedBackup import backupProcess, log_info
            self.logger.info("Successfully imported modules from virtual environment")
        except ImportError as e:
            self.logger.error(f"Failed to import modules: {str(e)}")
            self.logger.error(f"sys.path: {sys.path}")
            servicemanager.LogErrorMsg(f"Import error: {str(e)}")
            return
		
        startup()
        try:
            with dbConnector.dbConnector('10.113.162.55', 5432, 'postgres', 'postgres', 'postgres') as db:
                self.logger.info('Database connection established')
                
                while self.is_running:
                    try:
                        self.logger.info('Starting backup process')
                        log_info('backupProcess started', db)
                        backupProcess()
                        log_info('backupProcess finished', db)
                        self.logger.info('Backup process completed')
                        
                        # Check if service is stopping
                        for _ in range(30):  # 5 minute wait in 10-second increments
                            if win32event.WaitForSingleObject(self.stop_event, 10000) == win32event.WAIT_OBJECT_0:
                                break
                            
                    except Exception as e:
                        error_msg = f"Error in backup process: {str(e)}"
                        self.logger.error(error_msg)
                        self.logger.error(traceback.format_exc())
                        try:
                            log_info(f"Service error: {error_msg}", db)
                        except:
                            pass
                        
                        # Wait before retrying after error
                        # Wait before retrying after error
                        if win32event.WaitForSingleObject(self.stop_event, 60000) == win32event.WAIT_OBJECT_0:
                            break  # Exit if stop signal received
                        
        except Exception as e:
            self.logger.error(f"Critical service error: {str(e)}")
            self.logger.error(traceback.format_exc())
            servicemanager.LogErrorMsg(f"Critical service error: {str(e)}")



if __name__ == "__main__":
	#with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
		#s.settimeout(10)
		#client_socket.setblocking(0)
		
		#s.connect(('10.114.40.109', 9002))

		#print(byteArrayToHexString(plcReadMultipleBits(s, '410000', 'B4', 16, 50)))
		#print(byteArrayToHexString(plcReadMultipleWord(s, '590000', 'B4', 1, 50)))

	#readAllFiles('10.114.1.114', 9010, 50, '801.L1.AssyFront.UCDAM00031')
	#print("Hello, World!")

	#print(os.system("ping -n 1 10.114.40.240"))
	#resp = os.system("ping -n 1 10.114.40.240")
	#print(ping_ok('10.114.40.240'))

    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(PLCBackupService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(PLCBackupService)


	#startup()
	#with dbConnector.dbConnector('10.113.162.55', 5432, 'postgres', 'postgres', 'postgres') as db:
	#	while True:
	#		log_info('backupProcess started', db)
	#		backupProcess()
	#		log_info('backupProcess finished', db)
	#		time.sleep(300)



	#jstr = '202_稼働ﾓﾆﾀ'
	#print(jstr)
	#utf8_bytes = jstr.encode('utf-16') # Encode the string to bytes using utf-16
	#utf8_string = utf8_bytes.decode('utf-16').encode('utf-8').decode('utf-8') # Decode utf-16 and encode to utf-8
	#print(utf8_string)
	
	#testByteArray = 'hello'.encode('utf-16-le')
	#print(testByteArray)
	#hexValues = [f'{byte:02X}' for byte in testByteArray]
	#print(hexValues)