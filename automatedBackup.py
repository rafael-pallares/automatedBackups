import socket
import time
import datetime
import select
from io import BytesIO
from io import StringIO
#from StringIO import StringIO
import ftplib
import os
import subprocess
import logging


import win32serviceutil
import win32service
import win32event
import servicemanager

#from datetime import datetime, timedelta

import dbConnector
import const
import util

slmpRequestHeader = '500000FFFF0300'
backM = const.BackupMode.default_c

#logger = None

def send_message_byte_array(ip, port, wait_ticks, msg):
	
	# Create a socket connection
	client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	client_socket.settimeout(10)
	#client_socket.setblocking(0)
	
	client_socket.connect((ip, port))
	
    # Use BytesIO to collect the response
	return_out_stream = BytesIO()
    
    # Send the message
	client_socket.sendall(msg)

	countl = 0
	while True:
        # Check if there is data available to read
		ready_to_read = select.select([client_socket], [], [], 0)[0]
		if ready_to_read:
			#while True:
                # Read data from the socket
                #need to fix here, function will gte stuck reading socket
			data = client_socket.recv(1024)
			if not data:
				break
			return_out_stream.write(data)
                
			break
		else:
			time.sleep(0.01)  # Sleep for 100 milliseconds

		countl += 1
		if countl >= wait_ticks:
			break

    # Convert the BytesIO stream to bytes
	return_byte_array = return_out_stream.getvalue()
    
    # Clean up resources
	return_out_stream.close()
	client_socket.close()

	return return_byte_array

def sendMessageByteArraySocket(wait_ticks, msg, client_socket):	
	# Use BytesIO to collect the response
	return_out_stream = BytesIO()
	    
	# Send the message
	client_socket.sendall(msg)
	
	countl = 0
	while True:
	    # Check if there is data available to read
		ready_to_read = select.select([client_socket], [], [], 0)[0]
		if ready_to_read:
			#while True:
	            # Read data from the socket
	            #need to fix here, function will gte stuck reading socket
			data = client_socket.recv(2048)
			if not data:
				break
			return_out_stream.write(data)
	                
			break
		else:
			time.sleep(0.01)  # Sleep for 100 milliseconds
	
		countl += 1
		if countl >= wait_ticks:
			break
	
	    # Convert the BytesIO stream to bytes
	return_byte_array = return_out_stream.getvalue()
	    
	    # Clean up resources
	return_out_stream.close()
	
	return return_byte_array

def sendMessageByteArraySocketReadDirectories(wait_ticks, msg, client_socket):	
	# Use BytesIO to collect the response
	return_out_stream = BytesIO()
	    
	# Send the message
	client_socket.sendall(msg)
	
	countl = 0
	while True:
	    # Check if there is data available to read
		ready_to_read = select.select([client_socket], [], [], 0)
		firstResponse = True
		if len(ready_to_read) > 0 and ready_to_read[0]:
			#while True:
	        # Read data from the socket
	        #need to fix here, function will gte stuck reading socket
			data = client_socket.recv(2048)
			#print(bytes(data).hex())
			if not data:
				break
			if firstResponse:
				firstResponse = False
				if data[9] + data[10] != 0:
					break
			return_out_stream.write(data)
			currResp = byteArrayToHexString(return_out_stream.getvalue())
			#currResp = bytes(return_out_stream.getvalue()).hex()
			fileC = parseReadDirectoryFileCount(currResp)
			currFileC = len(parseReadDirectoryFileNames(currResp))
			currFileCnames = parseReadDirectoryFileNames(currResp)

			#print(data[9] + data[10])
			#print(fileC)
			#print(currFileC)
			#print(currFileCnames)


			if currFileC >= fileC:
				break
		else:
			time.sleep(0.01)  # Sleep for 100 milliseconds
		
		#if countr >= reRead:
		#	break
		
		countl += 1
		if countl >= wait_ticks:
			break
	
	    # Convert the BytesIO stream to bytes
	return_byte_array = return_out_stream.getvalue()
	    
	    # Clean up resources
	return_out_stream.close()
	
	return return_byte_array

def readFileCommand(ip, port, wait_ticks, filePointer, fileSize):
	offsetAddress = '00000000'
	offsetCounter = 0
	numberBytesRead = '8007'
	
	cmd = '28180000' + filePointer + offsetAddress + numberBytesRead
	
	rL = hex(int(float(len(cmd))/2) + 2)
	requestDataLen = rL.split('x')[1].upper() + '00'
	if len(requestDataLen) == 3:
		requestDataLen = '0' + requestDataLen
	msg = slmpRequestHeader + requestDataLen + '1000' + cmd
	#logger = system.util.getLogger('PlcBackup')
	#logger.info(msg)
	encMsg = bytes(bytearray.fromhex(msg))
	
	client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	client_socket.settimeout(10)
	#client_socket.setblocking(0)
		
	client_socket.connect((ip, port))
		
	# Use BytesIO to collect the response
	return_out_stream = BytesIO()
	    
	# Send the message
	while offsetCounter < fileSize:
		client_socket.sendall(encMsg)
		
		countl = 0
		readSize = 0
		readSizeTotal = 1920
		while True:
		    # Check if there is data available to read
			ready_to_read = select.select([client_socket], [], [], 0)[0]
			if ready_to_read:
				#while True:
		            # Read data from the socket
		            #need to fix here, function will gte stuck reading socket
				data = client_socket.recv(4096)
				if not data:
					break
				if readSize == 0:
					#readSizeTotal = int('0x' + data[12].encode('hex') + data[11].encode('hex'), 16)
					readSizeTotal = int('0x' + byteArrayToHexString([data[12], data[11]]), 0)
					return_out_stream.write(data[13:])
				else:
					return_out_stream.write(data)
				readSize += len(data)
				if readSize >= readSizeTotal:
					break
			else:
				time.sleep(0.01)  # Sleep for 100 milliseconds
		
			countl += 1
			if countl >= wait_ticks:
				break
		offsetCounter += 1920
		newOff = hex(offsetCounter).split('x')[1].upper()
		if len(newOff) == 3:
			offsetAddress = newOff[1] + newOff[2] + '0' + newOff[0] + '0000'
		elif len(newOff) == 4:
			offsetAddress = newOff[2] + newOff[3] + newOff[0] + newOff[1] + '0000'
		elif len(newOff) == 5:
			offsetAddress = newOff[3] + newOff[4] + newOff[1] + newOff[2] + '0' + newOff[0] + '00'
		else:
			offsetAddress = newOff[4] + newOff[5] + newOff[2] + newOff[3] + newOff[0] + newOff[1] + '00'
		
		remainingByes = fileSize - offsetCounter
		if remainingByes < 1920:
			newNumBytRea = hex(remainingByes).split('x')[1].upper()
			if len(newNumBytRea) == 1:
				numberBytesRead = '0' + newNumBytRea + '00'
			elif len(newNumBytRea) == 2:
				numberBytesRead = newNumBytRea + '00'
			else:
				numberBytesRead = newNumBytRea[1] + newNumBytRea[2] + '0' + newNumBytRea[0]
				
		
		cmd = '28180000' + filePointer + offsetAddress + numberBytesRead
		msg = slmpRequestHeader + requestDataLen + '1000' + cmd
		encMsg = bytes(bytearray.fromhex(msg))
	
	client_socket.close()
	
	return return_out_stream

def readFileSocket(wait_ticks, filePointer, fileSize, client_socket):
	offsetAddress = '00000000'
	offsetCounter = 0
	
	numberBytesRead = '0000'
	if fileSize < 1920:
		newNumBytRea = hex(fileSize).split('x')[1].upper()
		if len(newNumBytRea) == 1:
			numberBytesRead = '0' + newNumBytRea + '00'
		elif len(newNumBytRea) == 2:
			numberBytesRead = newNumBytRea + '00'
		else:
			numberBytesRead = newNumBytRea[1] + newNumBytRea[2] + '0' + newNumBytRea[0]
	else:
		numberBytesRead = '8007'
	
	cmd = '28180000' + filePointer + offsetAddress + numberBytesRead
	
	rL = hex(int(float(len(cmd))/2) + 2)
	requestDataLen = rL.split('x')[1].upper() + '00'
	if len(requestDataLen) == 3:
		requestDataLen = '0' + requestDataLen
	msg = slmpRequestHeader + requestDataLen + '1000' + cmd
	#logger = system.util.getLogger('PlcBackup')
	#logger.info(msg)
	encMsg = bytes(bytearray.fromhex(msg))
	
	#client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	#client_socket.settimeout(10)
	#client_socket.setblocking(0)
		
	#client_socket.connect((ip, port))
		
	# Use BytesIO to collect the response
	return_out_stream = BytesIO()
	    
	# Send the message
	while offsetCounter < fileSize:
		client_socket.sendall(encMsg)
		
		countl = 0
		readSize = 0
		readSizeTotal = 0
		timeoutEr = False
		readZeroCount = 0
		while True:
		    # Check if there is data available to read
			ready_to_read = select.select([client_socket], [], [], 0)[0]
			if ready_to_read:#while True:
				#while True:
		            # Read data from the socket
		            #need to fix here, function will gte stuck reading socket
				try:
					data = client_socket.recv(2048)
					if not data:
						break
					if readSize == 0:
						#readSizeTotal = int('0x' + data[12].encode('hex') + data[11].encode('hex'), 16)
						if len(data) < 14:
							log_info_nodb('length of data too short. Message sent: ' + msg)
							log_info_nodb('length of data too short. readsize, readSizeTotal, offsetCounter, fileSize: ' + str(readSize)
					 			+ ', ' + str(readSizeTotal) + ', ' + str(offsetCounter) + ', ' + str(fileSize))
							log_info_nodb('length of data too short: ' + str(len(data)) + ' data: ' + byteArrayToHexString(data))
							timeoutEr = True
							break
						readSizeTotal = int('0x' + byteArrayToHexString([data[12], data[11]]), 0)
						return_out_stream.write(data[13:])
					else:
						return_out_stream.write(data)
					readSize += len(data)
					if readSize >= readSizeTotal:
						break
					if len(data) == 0:
						log_info_nodb('length was 0!')
						readZeroCount += 1
						if readZeroCount > 49:
							break
				except socket.timeout:
					print(readSize)
					print(readSizeTotal)
					print(offsetCounter)
					print(fileSize)
					print(data)
					timeoutEr = True
					break
			else:
				time.sleep(0.001)  # Sleep for 1 milliseconds
		
			#countl += 1
			#if countl >= wait_ticks:
			#	break
		offsetCounter += 1920
		#if offsetCounter % 100000 <= 1920:
			#logger.info(str(offsetCounter))
		newOff = hex(offsetCounter).split('x')[1].upper()
		if len(newOff) == 3:
			offsetAddress = newOff[1] + newOff[2] + '0' + newOff[0] + '0000'
		elif len(newOff) == 4:
			offsetAddress = newOff[2] + newOff[3] + newOff[0] + newOff[1] + '0000'
		elif len(newOff) == 5:
			offsetAddress = newOff[3] + newOff[4] + newOff[1] + newOff[2] + '0' + newOff[0] + '00'
		elif len(newOff) == 6:
			offsetAddress = newOff[4] + newOff[5] + newOff[2] + newOff[3] + newOff[0] + newOff[1] + '00'
		else:
			offsetAddress = newOff[5] + newOff[6] + newOff[3] + newOff[4] + newOff[1] + newOff[2] + '0' + newOff[0]
		
		remainingByes = fileSize - offsetCounter
		if remainingByes < 1920:
			newNumBytRea = hex(remainingByes).split('x')[1].upper()
			if len(newNumBytRea) == 1:
				numberBytesRead = '0' + newNumBytRea + '00'
			elif len(newNumBytRea) == 2:
				numberBytesRead = newNumBytRea + '00'
			else:
				numberBytesRead = newNumBytRea[1] + newNumBytRea[2] + '0' + newNumBytRea[0]
				
		
		cmd = '28180000' + filePointer + offsetAddress + numberBytesRead
		msg = slmpRequestHeader + requestDataLen + '1000' + cmd
		encMsg = bytes(bytearray.fromhex(msg))

		if timeoutEr:
			break
	#client_socket.close()
	
	return return_out_stream.getvalue()

def openReadCloseFileSocket(wait_ticks, driveN, fileName, fileSize, clientSocket):
	
	openResp = openFileSocket(wait_ticks, driveN, fileName, clientSocket)
	#logger.info(openResp)
	log_info_nodb('open response: ' + openResp)
	if openResp[18:22] == '0000':
		fileP = openResp[-4:]
		fileData = readFileSocket(wait_ticks, fileP, fileSize, clientSocket)
		log_info_nodb('fileData size: ' + str(len(fileData)))

		closeResp = closeFileSocket(wait_ticks, fileP, clientSocket)
		#logger.info(closeResp)
		return fileData
	else:
		#logger.info(openResp)
		#print(fileName)
		#print(openResp)

		#should add here logging of failed open files!!

		closeResp = closeFileSocket(wait_ticks, '0000', clientSocket)
		#logger.info(closeResp)
		return []

def readMultipleFiles(wait_ticks, driveN, fileDict, ftp, clientSocket):
	log_info_nodb('file list: ' + str(fileDict))
	for key, value in fileDict.items():
		#if value > 0 and 'COMMENT.DCM' not in key:
		if value > 0:
			log_info_nodb('reading file: ' + key)
			fileD = openReadCloseFileSocket(wait_ticks, driveN, key, value, clientSocket)
			if len(fileD) > 0:
				#stringio = StringIO(fileD)
				stringio = BytesIO(fileD)
				#logger.info(str(len(fileD)))
				
				#print(key.split('\\')[-1])
				utf8_bytes = key.split('\\')[-1].encode('utf-16') # Encode the string to bytes using utf-16
				utf8_string = utf8_bytes.decode('utf-16').encode('utf-8').decode('utf-8') # Decode utf-16 and encode to utf-8
				#print(utf8_string)

				ftp.storbinary('STOR ' + utf8_string, stringio)
			time.sleep(0.01)

def readAllFiles(ip, port, wait_ticks, ftpPath):
	#logger = system.util.getLogger('PlcBackup')
	# Create a socket connection
	client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	client_socket.settimeout(10)
	#client_socket.setblocking(0)
	
	#logger.info('Backup start for ' + ip)
	print('Backup start for ' + ip)
	try:
		ftp = None
		client_socket.connect((ip, port))
		directories = ['']
		fileDictionary2 = {}
		fileDictionary3 = {}
		fileDictionary4 = {}
		while directories:
			dirRead = directories.pop(0)
			newFileDict = readDirectoriesSocket(wait_ticks, 2, dirRead, client_socket)
			#logger.info(dirRead)
			
			for key, value in newFileDict.items():
				if value == 0 and key != '.' and key != '..':
					if dirRead != '':
						directories.append(dirRead + '\\' + key)
					else:
						directories.append(key)
				elif value > 0:
					if dirRead != '':
						fileDictionary2[dirRead + '\\' + key] = value
					else:
						fileDictionary2[key] = value
		
		directories = ['']
		while directories:
			dirRead = directories.pop(0)
			newFileDict = readDirectoriesSocket(wait_ticks, 3, dirRead, client_socket)
			#logger.info(dirRead)
			
			for key, value in newFileDict.items():
				if value == 0 and key != '.' and key != '..':
					if dirRead != '':
						directories.append(dirRead + '\\' + key)
					else:
						directories.append(key)
				elif value > 0:
					if dirRead != '':
						fileDictionary3[dirRead + '\\' + key] = value
					else:
						fileDictionary3[key] = value
		
		directories = ['']
		while directories:
			dirRead = directories.pop(0)
			newFileDict = readDirectoriesSocket(wait_ticks, 4, dirRead, client_socket)
			#logger.info(dirRead)
			
			for key, value in newFileDict.items():
				if value == 0 and key != '.' and key != '..':
					if dirRead != '':
						directories.append(dirRead + '\\' + key)
					else:
						directories.append(key)
				elif value > 0:
					if dirRead != '':
						fileDictionary4[dirRead + '\\' + key] = value
					else:
						fileDictionary4[key] = value
		
		#logger.info(str(fileDictionary2))
		#logger.info(str(fileDictionary3))
		#logger.info(str(fileDictionary4))
		#print(fileDictionary2)
		#print(fileDictionary3)
		#print(fileDictionary4)
		
		
		ftp = ftplib.FTP('10.113.162.55')
		ftp.login('testuser','1234')
		#logger.info(ftp.getwelcome())
		print(ftp.getwelcome())
		ftp.cwd('test01')
		#logger.info(str(ftp.nlst()))
		for fol in ftpPath.split('.'):
			directList = ftp.nlst()
			if fol in directList:
				ftp.cwd(fol)
			else:
				ftp.mkd(fol)
				ftp.cwd(fol)
		currentTime = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
		ftp.mkd(currentTime)
		ftp.cwd(currentTime)
		ftp.mkd('2')
		ftp.cwd('2')
		ftp.mkd('$MELPRJ$')
		ftp.cwd('$MELPRJ$')
		
		fileDict = {}
		#fileDict['$MELPRJ$\\COMMENT.DCM'] =  2000000
		fileDict['$MELPRJ$\\COMMENT.DCM'] = 33494196
		#fileDict['$MELPRJ$\\010.PRG'] = 34436
		#fileDict['$MELPRJ$\\028.PRG'] = 2200
		#fileDict['$MELPRJ$\\010.PRG'] = 2200
		
		#readMultipleFiles(wait_ticks, 2, fileDict, ftp, client_socket)
		if backM == const.BackupMode.full:
			readMultipleFiles(wait_ticks, 2, fileDictionary2, ftp, client_socket)
		elif backM == const.BackupMode.default_c:
			readMultipleFiles(wait_ticks, 2, util.filter_dictionary_by_key(fileDictionary2, '$MELPRJ$\\COMMENT.DCM'), ftp, client_socket)
		
		ftp.cwd("..")
		ftp.cwd("..")
		ftp.mkd('3')
		ftp.cwd('3')
		ftp.mkd('$MELPRJ$')
		ftp.cwd('$MELPRJ$')
		
		readMultipleFiles(wait_ticks, 3, fileDictionary3, ftp, client_socket)
		
		ftp.cwd("..")
		ftp.cwd("..")
		ftp.mkd('4')
		ftp.cwd('4')
		ftp.mkd('$MELPRJ$')
		ftp.cwd('$MELPRJ$')
		
		readMultipleFiles(wait_ticks, 4, fileDictionary4, ftp, client_socket)
		
		#client_socket.close()
		
		#ftp.quit()
	#except Exception as e:
	#	logger.info(str(e))
	finally:
		client_socket.close()
		if ftp is not None:  # Check if ftp was created
			ftp.quit()  # Close the FTP connection
		#logger.info('Backup finish for ' + ip)
		print('Backup finish for ' + ip)

def readDirectories(ip, port, wait_ticks, driveN, directPath):
	fileDict = {}
	
	driveNumber = '0' + str(driveN) + '00'
	headFileNumber = '01000000'
	numberOfRequestedFiles = '2400'
	
	#numberDirectoryPathNameChar = '0800'
	#directoryPathName = '24004D0045004C00500052004A002400'
	
	directoryPathName = ''
	if directPath == '':
		numberDirectoryPathNameChar = '0000'
	else:
		if len(directPath) < 16:
			numberDirectoryPathNameChar = '0' + hex(len(directPath)).split('x')[1].upper() + '00'
		else:
			numberDirectoryPathNameChar = hex(len(directPath)).split('x')[1].upper() + '00'
		for c in directPath:
			directoryPathName += format(ord(c), 'x') + '00'
	
	cmd = '1018400000000000' + driveNumber + headFileNumber + numberOfRequestedFiles + numberDirectoryPathNameChar + directoryPathName
	
	requestDataLen = hex(int(float(len(cmd))/2) + 2).split('x')[1].upper() + '00'
	
	msg = slmpRequestHeader + requestDataLen + '1000' + cmd
	#msg = '500000FFFF03002400100010184000000000000400010000002400080024004D0045004C00500052004A002400'
	
	encMsg = bytes(bytearray.fromhex(msg))
	
	# Create a socket connection
	client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	client_socket.settimeout(10)
	#client_socket.setblocking(0)
	
	client_socket.connect((ip, port))
	
	remainingFiles = True
	while remainingFiles:
		resp = byteArrayToHexString(sendMessageByteArraySocketReadDirectories(wait_ticks, encMsg, client_socket))
		fileN = parseReadDirectoryFileNames(resp)
		fileS = parseReadDirectoryFileSizes(resp)
		for key, value in zip(fileN, fileS):
			fileDict[key] = value
		if parseReadDirectoryFileCount(resp) == 0:
			remainingFiles = False
			break
		newHeadFileNo = intToHexString(parseReadDirectoryEndFileNo(resp) + 1)
		if len(newHeadFileNo) == 1:
			headFileNumber = '0' + newHeadFileNo + '000000'
		elif len(newHeadFileNo) == 2:
			headFileNumber = newHeadFileNo + '000000'
		else:
			headFileNumber = newHeadFileNo[1] + newHeadFileNo[2] + '0' + newHeadFileNo[0] + '0000'
		
		#logger = system.util.getLogger('PlcBackup')
		#logger.info(resp)
		
		cmd = '1018400000000000' + driveNumber + headFileNumber + numberOfRequestedFiles + numberDirectoryPathNameChar + directoryPathName
		msg = slmpRequestHeader + requestDataLen + '1000' + cmd
		encMsg = bytes(bytearray.fromhex(msg))
	
	client_socket.close()
	
	return fileDict

def openFileCommand(ip, port, wait_ticks, fileName):
	cmd = '27184000000000000400'
	fileNameLen = hex(len(fileName)).split('x')[1].upper() + '00'
	fileNameHex = ''
	for c in fileName:
		fileNameHex += format(ord(c), 'x') + '00'
	requestDataLen = hex(int(float(len(cmd + fileNameLen + fileNameHex))/2) + 2).split('x')[1].upper() + '00'
	
	msg = slmpRequestHeader + requestDataLen + '1000' + cmd + fileNameLen + fileNameHex
	encMsg = bytes(bytearray.fromhex(msg))
	
	return byteArrayToHexString(send_message_byte_array(ip, port, wait_ticks, encMsg))

def closeFileCommand(ip, port, wait_ticks, filePointer):
	cmd = '2A180000' + filePointer + '0100'
	
	rL = int(float(len(cmd))/2)
	requestDataLen = hex(rL + 2).split('x')[1].upper() + '00'
	if len(requestDataLen) == 3:
		requestDataLen = '0' + requestDataLen
	msg = slmpRequestHeader + requestDataLen + '1000' + cmd
	#logger = system.util.getLogger('PlcBackup')
	#logger.info(msg)
	encMsg = bytes(bytearray.fromhex(msg))
	return byteArrayToHexString(send_message_byte_array(ip, port, wait_ticks, encMsg))







def send_message_string(ip, port, wait_ticks, msg):
	# Create a socket connection
	client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	client_socket.settimeout(10)
	#client_socket.setblocking(0)
	
	client_socket.connect((ip, port))
	
    # Use BytesIO to collect the response
	#return_out_stream = BytesIO()
	
	HEX_ARRAY = '0123456789ABCDEF'
	resp = ''
    
    # Send the message
	client_socket.sendall(msg)

	countl = 0
	while True:
        # Check if there is data available to read
		ready_to_read = select.select([client_socket], [], [], 0)[0]
		if ready_to_read:
			while True:
                # Read data from the socket
                #need to fix here, function will gte stuck reading socket
				data = client_socket.recv(1)
				if not data:
					break
				#return_out_stream.write(data)
				resp += data.decode("utf-8")
                
		else:
			time.sleep(0.01)  # Sleep for 100 milliseconds

		countl += 1
		if countl >= wait_ticks:
			resp += 'timed out!'
			break

    # Convert the BytesIO stream to bytes
	#return_byte_array = return_out_stream.getvalue()
    
    # Clean up resources
	#return_out_stream.close()
	client_socket.close()

	return resp

def readDirectoriesSocket(wait_ticks, driveN, directPath, client_socket):
	fileDict = {}
	
	driveNumber = '0' + str(driveN) + '00'
	headFileNumber = '01000000'
	numberOfRequestedFiles = '2400'
	
	#numberDirectoryPathNameChar = '0800'
	#directoryPathName = '24004D0045004C00500052004A002400'
	
	directoryPathName = ''
	if directPath == '':
		numberDirectoryPathNameChar = '0000'
	else:
		if len(directPath) < 16:
			numberDirectoryPathNameChar = '0' + hex(len(directPath)).split('x')[1].upper() + '00'
		else:
			numberDirectoryPathNameChar = hex(len(directPath)).split('x')[1].upper() + '00'
		directPathb = directPath.encode('utf-16-le')
		for b in directPathb:
			directoryPathName += f'{b:02X}'
		#if directoryPathName[0] == '2':
		#	print(directoryPathName)
		#	for by in directPathb:
		#		print(str(by))
		#for c in directPath:
		#	directoryPathName += format(ord(c), 'x') + '00'
	
	cmd = '1018400000000000' + driveNumber + headFileNumber + numberOfRequestedFiles + numberDirectoryPathNameChar + directoryPathName
	
	requestDataLen = hex(int(float(len(cmd))/2) + 2).split('x')[1].upper() + '00'
	
	msg = slmpRequestHeader + requestDataLen + '1000' + cmd
	#msg = '500000FFFF03002400100010184000000000000400010000002400080024004D0045004C00500052004A002400'
	#print(msg)

	encMsg = bytes(bytearray.fromhex(msg))
	
	#print(str(encMsg))
	# Create a socket connection
	#client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	#client_socket.settimeout(10)
	#client_socket.setblocking(0)
	
	#client_socket.connect((ip, port))
	
	remainingFiles = True
	while remainingFiles:
		resp = byteArrayToHexString(sendMessageByteArraySocketReadDirectories(wait_ticks, encMsg, client_socket))
		fileN = parseReadDirectoryFileNames(resp)
		fileS = parseReadDirectoryFileSizes(resp)
		for key, value in zip(fileN, fileS):
			fileDict[key] = value
		if parseReadDirectoryFileCount(resp) == 0:
			remainingFiles = False
			break
		newHeadFileNo = intToHexString(parseReadDirectoryEndFileNo(resp) + 1)
		if newHeadFileNo == '10000':
			remainingFiles = False
			break	
		if len(newHeadFileNo) == 1:
			headFileNumber = '0' + newHeadFileNo + '000000'
		elif len(newHeadFileNo) == 2:
			headFileNumber = newHeadFileNo + '000000'
		elif len(newHeadFileNo) == 3:
			headFileNumber = newHeadFileNo[1] + newHeadFileNo[2] + '0' + newHeadFileNo[0] + '0000'
		elif len(newHeadFileNo) == 4:
			headFileNumber = newHeadFileNo[2] + newHeadFileNo[3] + newHeadFileNo[0] + newHeadFileNo[1] + '0000'
		elif len(newHeadFileNo) == 5:
			headFileNumber = newHeadFileNo[3] + newHeadFileNo[4] + newHeadFileNo[1] + newHeadFileNo[2] + '0'+ newHeadFileNo[0] + '00'
		elif len(newHeadFileNo) == 6:
			headFileNumber = newHeadFileNo[4] + newHeadFileNo[5] + newHeadFileNo[2] + newHeadFileNo[3] + newHeadFileNo[0] + newHeadFileNo[1] + '00'
		elif len(newHeadFileNo) == 7:
			headFileNumber = newHeadFileNo[5] + newHeadFileNo[6] + newHeadFileNo[3] + newHeadFileNo[4] + newHeadFileNo[1] + newHeadFileNo[2] + '0' + newHeadFileNo[0]
		elif len(newHeadFileNo) == 8:
			headFileNumber = newHeadFileNo[6] + newHeadFileNo[7] + newHeadFileNo[4] + newHeadFileNo[5] + newHeadFileNo[2] + newHeadFileNo[3] + newHeadFileNo[0] + newHeadFileNo[1]
		else:
			headFileNumber = 'FFFFFFFF'
		
		#print(newHeadFileNo)
		#print(headFileNumber)
		
		#logger = system.util.getLogger('PlcBackup')
		#logger.info(resp)
		
		cmd = '1018400000000000' + driveNumber + headFileNumber + numberOfRequestedFiles + numberDirectoryPathNameChar + directoryPathName
		msg = slmpRequestHeader + requestDataLen + '1000' + cmd
		encMsg = bytes(bytearray.fromhex(msg))
	
	#client_socket.close()
	
	return fileDict

def closeFileSocket(wait_ticks, filePointer, clientSocket):
	cmd = '2A180000' + filePointer + '0100'
	
	rL = int(float(len(cmd))/2)
	requestDataLen = hex(rL + 2).split('x')[1].upper() + '00'
	if rL < 16:
		requestDataLen = '0' + requestDataLen
	msg = slmpRequestHeader + requestDataLen + '1000' + cmd
	#logger = system.util.getLogger('PlcBackup')
	#logger.info(msg)
	encMsg = bytes(bytearray.fromhex(msg))
	return byteArrayToHexString(sendMessageByteArraySocket(wait_ticks, encMsg, clientSocket))

def openFileSocket(wait_ticks, driveN, fileName, clientSocket):
	cmd = '2718400000000000'
	driveNumber = '0' + str(driveN) + '00'
	fileNameLen = hex(len(fileName)).split('x')[1].upper() + '00'
	if len(fileNameLen) == 3:
		fileNameLen = '0' + fileNameLen
	fileNameHex = ''
	filenameb = fileName.encode('utf-16-le')
	for b in filenameb:
		fileNameHex += f'{b:02X}'
	
	#if fileName == '$MELPRJ$\\202_<竍傓ﾆﾀＮPRG' or fileName == '$MELPRJ$\·ミュレータ〮PRG':
	#	print(fileName + ' hex value:')
	#	print(fileNameHex)
	#for c in fileName:
	#	fileNameHex += format(ord(c), 'x') + '00'
	requestDataLen = hex(int(float(len(cmd + driveNumber + fileNameLen + fileNameHex))/2) + 2).split('x')[1].upper() + '00'
	
	msg = slmpRequestHeader + requestDataLen + '1000' + cmd + driveNumber + fileNameLen + fileNameHex
	encMsg = bytes(bytearray.fromhex(msg))
	
	return byteArrayToHexString(sendMessageByteArraySocket(wait_ticks, encMsg, clientSocket))

def byteArrayToHexString(byteA):
	#converts a byte array t a hex string
	#hexString = ''
	#for by in byteA:
		#hexString += by.encode('hex')
	#	hexString += f'{by:x}'
	
	#return hexString
	return bytes(byteA).hex()



def intToHexString(num):
	return hex(num).split('x')[1].upper()

def parseReadDirectoryFilePointers(response):
	#function that parses response from read directory command and returs and array with the file names
	filePointers = []
	if len(response) < 23:
		return filePointers
	fileCount = int('0x' + response[22] + response[23], 16)
	ind = 34
	for i in range(fileCount):
		if(ind < len(response)):
			fileNameSize = int('0x' + response[ind] + response[ind + 1], 16)
			
			add = 34 + (fileNameSize*4)

			filePointer = int('0x' + response[ind + add + 2] + response[ind + add + 3] + response[ind + add] + response[ind + add + 1], 16)
				
			filePointers.append(filePointer)
			
			ind += 46 + (fileNameSize * 4)
		else:
			break
	
	return filePointers

def parseReadDirectoryEndFileNo(response):
	if len(response) > 33:
		endFileNo = int('0x' + response[32] + response[33] + response[30] + response[31] + response[28] + response[29] + response[26] + response[27], 16)
		return endFileNo
	else:
		return 0

def parseReadDirectoryFileSizes(response):
	#function that parses response from read directory command and returs and array with the file names
	fileSizes = []
	if len(response) < 23:
		return fileSizes
	fileCount = int('0x' + response[22] + response[23], 16)
	ind = 34
	for i in range(fileCount):
		if(ind < len(response)):
			fileNameSize = int('0x' + response[ind] + response[ind + 1], 16)
			if(ind + 45 + ((fileNameSize*4)) < len(response)):
				add = 38 + (fileNameSize*4)
	
				fileSize = int('0x' + response[ind + add + 6] + response[ind + add + 7] + response[ind + add + 4] + response[ind + add + 5] 
					+ response[ind + add + 2] + response[ind + add + 3] + response[ind + add] + response[ind + add + 1], 16)
					
				fileSizes.append(fileSize)
				
				ind += 46 + (fileNameSize * 4)
			else:
				break
		else:
			break
	
	return fileSizes

def parseReadDirectoryFileCount(response):
	if len(response) > 25:
		#fileCount = int('0x' + response[24] + response[25] + response[22] + response[23], 16)
		fileCount = int('0x' + response[24] + response[25] + response[22] + response[23], 0)
		#print(response[24] + response[25] + response[22] + response[23])
		return fileCount
	else:
		return 0

def parseReadDirectoryFileNames(response):
	#function that parses response from read directory command and returs and array with the file names
	fileNames = []
	if len(response) < 23:
		return fileNames
	#fileCount = int('0x' + response[22] + response[23], 16)
	fileCount = int('0x' + response[22] + response[23], 0)
	ind = 34
	for i in range(fileCount):
		if(ind < len(response)):
			#fileNameSize = int('0x' + response[ind] + response[ind + 1], 16)
			fileNameSize = int('0x' + response[ind] + response[ind + 1], 0)
			if(ind + 5 + (fileNameSize * 4) < len(response)):
				fileNameHex = ''
				for j in range(fileNameSize):
					fileNameHex += response[ind + 2 + (j * 4)] + response[ind + 3 + (j * 4)] + response[ind + 4 + (j * 4)] + response[ind + 5 + (j * 4)]
				#fileName = fileNameHex.decode('hex')
				try:
					fileName = bytearray.fromhex(fileNameHex).decode('utf-16-be')
					#if fileName[0] == '2':
					#	print(fileName)
					#	print(fileNameHex)
					fileNames.append(fileName)
				except Exception as e:
					print(str(e))
					print(fileNameHex)
					print(response)
				finally:
					ind += 46 + (fileNameSize * 4)
			else:
				break
		else:
			break
	
	return fileNames




def plcReadBit(clientSocket, headDeviceNo, deviceCode, wait_ticks):
	cmd = '01040100' + headDeviceNo + deviceCode + '0100'
	#cmd = '1018400000000000' + driveNumber + headFileNumber + numberOfRequestedFiles + numberDirectoryPathNameChar + directoryPathName
	
	requestDataLen = hex(int(float(len(cmd))/2) + 2).split('x')[1].upper() + '00'
	if len(requestDataLen) == 3:
		requestDataLen = '0' + requestDataLen
	
	msg = slmpRequestHeader + requestDataLen + '1000' + cmd

	print(requestDataLen)

	encMsg = bytes(bytearray.fromhex(msg))

	return_out_stream = BytesIO()
	    
	# Send the message
	clientSocket.sendall(encMsg)
	
	countl = 0
	while True:
	    # Check if there is data available to read
		ready_to_read = select.select([clientSocket], [], [], 0)[0]
		if ready_to_read:
			#while True:
	            # Read data from the socket
	            #need to fix here, function will gte stuck reading socket
			data = clientSocket.recv(2048)
			if not data:
				break
			return_out_stream.write(data)
	                
			break
		else:
			time.sleep(0.01)  # Sleep for 100 milliseconds
	
		countl += 1
		if countl >= wait_ticks:
			break
	
	    # Convert the BytesIO stream to bytes
	return_byte_array = return_out_stream.getvalue()
	    
	    # Clean up resources
	return_out_stream.close()
	
	return return_byte_array

def plcReadMultipleBits(clientSocket, headDeviceNo, deviceCode, numberOfPoints, wait_ticks):
	
	numberOfPointsHex = hex(numberOfPoints).split('x')[1].upper()
	if len(numberOfPointsHex) < 3:
		numberOfPointsHex = numberOfPointsHex + '00'
		if len(numberOfPointsHex) == 3:
			numberOfPointsHex = '0' + numberOfPointsHex
	elif len(numberOfPointsHex) == 3:
		numberOfPointsHex = numberOfPointsHex[1] + numberOfPointsHex[2] + '0' + numberOfPointsHex[0]
	else:
		numberOfPointsHex = numberOfPointsHex[2] + numberOfPointsHex[3] + numberOfPointsHex[0] + numberOfPointsHex[1]
	
	cmd = '01040100' + headDeviceNo + deviceCode + numberOfPointsHex
	#cmd = '1018400000000000' + driveNumber + headFileNumber + numberOfRequestedFiles + numberDirectoryPathNameChar + directoryPathName
	
	requestDataLen = hex(int(float(len(cmd))/2) + 2).split('x')[1].upper() + '00'
	if len(requestDataLen) == 3:
		requestDataLen = '0' + requestDataLen
	
	msg = slmpRequestHeader + requestDataLen + '1000' + cmd

	print(requestDataLen)

	encMsg = bytes(bytearray.fromhex(msg))

	return_out_stream = BytesIO()
	    
	# Send the message
	clientSocket.sendall(encMsg)
	
	countl = 0
	while True:
	    # Check if there is data available to read
		ready_to_read = select.select([clientSocket], [], [], 0)[0]
		if ready_to_read:
			#while True:
	            # Read data from the socket
	            #need to fix here, function will gte stuck reading socket
			data = clientSocket.recv(2048)
			if not data:
				break
			return_out_stream.write(data)
	                
			break
		else:
			time.sleep(0.01)  # Sleep for 100 milliseconds
	
		countl += 1
		if countl >= wait_ticks:
			break
	
	    # Convert the BytesIO stream to bytes
	return_byte_array = return_out_stream.getvalue()
	    
	    # Clean up resources
	return_out_stream.close()
	
	return return_byte_array

def plcReadWord(clientSocket, headDeviceNo, deviceCode, wait_ticks):
	cmd = '01040000' + headDeviceNo + deviceCode + '0100'
	#cmd = '1018400000000000' + driveNumber + headFileNumber + numberOfRequestedFiles + numberDirectoryPathNameChar + directoryPathName
	
	requestDataLen = hex(int(float(len(cmd))/2) + 2).split('x')[1].upper() + '00'
	if len(requestDataLen) == 3:
		requestDataLen = '0' + requestDataLen
	
	msg = slmpRequestHeader + requestDataLen + '1000' + cmd

	#print(requestDataLen)

	encMsg = bytes(bytearray.fromhex(msg))

	return_out_stream = BytesIO()
	    
	# Send the message
	clientSocket.sendall(encMsg)
	
	countl = 0
	while True:
	    # Check if there is data available to read
		ready_to_read = select.select([clientSocket], [], [], 0)[0]
		if ready_to_read:
			#while True:
	            # Read data from the socket
	            #need to fix here, function will gte stuck reading socket
			data = clientSocket.recv(2048)
			if not data:
				break
			return_out_stream.write(data)
	                
			break
		else:
			time.sleep(0.01)  # Sleep for 100 milliseconds
	
		countl += 1
		if countl >= wait_ticks:
			break
	
	    # Convert the BytesIO stream to bytes
	return_byte_array = return_out_stream.getvalue()
	    
	    # Clean up resources
	return_out_stream.close()
	
	return return_byte_array

def plcReadMultipleWord(clientSocket, headDeviceNo, deviceCode, numberOfPoints, wait_ticks):
	numberOfPointsHex = hex(numberOfPoints).split('x')[1].upper()
	if len(numberOfPointsHex) < 3:
		numberOfPointsHex = numberOfPointsHex + '00'
		if len(numberOfPointsHex) == 3:
			numberOfPointsHex = '0' + numberOfPointsHex
	elif len(numberOfPointsHex) == 3:
		numberOfPointsHex = numberOfPointsHex[1] + numberOfPointsHex[2] + '0' + numberOfPointsHex[0]
	else:
		numberOfPointsHex = numberOfPointsHex[2] + numberOfPointsHex[3] + numberOfPointsHex[0] + numberOfPointsHex[1]

	
	cmd = '01040000' + headDeviceNo + deviceCode + numberOfPointsHex
	#cmd = '1018400000000000' + driveNumber + headFileNumber + numberOfRequestedFiles + numberDirectoryPathNameChar + directoryPathName
	
	requestDataLen = hex(int(float(len(cmd))/2) + 2).split('x')[1].upper() + '00'
	if len(requestDataLen) == 3:
		requestDataLen = '0' + requestDataLen
	
	msg = slmpRequestHeader + requestDataLen + '1000' + cmd

	#print(requestDataLen)

	encMsg = bytes(bytearray.fromhex(msg))

	return_out_stream = BytesIO()
	    
	# Send the message
	clientSocket.sendall(encMsg)
	
	countl = 0
	while True:
	    # Check if there is data available to read
		ready_to_read = select.select([clientSocket], [], [], 0)[0]
		if ready_to_read:
			#while True:
	            # Read data from the socket
	            #need to fix here, function will gte stuck reading socket
			data = clientSocket.recv(2048)
			if not data:
				break
			return_out_stream.write(data)
	                
			break
		else:
			time.sleep(0.01)  # Sleep for 100 milliseconds
	
		countl += 1
		if countl >= wait_ticks:
			break
	
	    # Convert the BytesIO stream to bytes
	return_byte_array = return_out_stream.getvalue()
	    
	    # Clean up resources
	return_out_stream.close()
	
	return return_byte_array

def ping_ok(sHost) -> bool:
    try:
        subprocess.check_output(
            "ping -{} 1 {}".format("n", sHost), shell=True
        )
    except Exception:
        return False

    return True


def backupProcess():
	with dbConnector.dbConnector('10.113.162.55', 5432, 'postgres', 'postgres', 'postgres') as db:
		cols = ['"AssetCode"', '"ftpPath"', '"IPaddress"', '"Port"', '"machine_id"', 'connected']
		wh = ['"Enabled"']

		allPlcs = db.selectWhere(cols, '"BackupAssets"', wh, (True,))
		for plc in allPlcs:
			if(ping_ok(plc[2])):
				db.updateValues(['connected'], '"BackupAssets"', (True, plc[4]), ['machine_id'])
				with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
					s.settimeout(10)
					try:
						s.connect((plc[2], plc[3]))
					except Exception as e:
						print(e)
						if "[WinError 10061]" in str(e):
							log_info(plc[0] + ' - ' + plc[2] + ' - ' + str(e) + ' - This can happen if specified port is not open or is '\
								'already being used by something else. PLC will be disabled, it will have to be anabled manually once '\
								'port is opened' , db)
							db.updateValues(['"Enabled"', 'connected'], '"BackupAssets"', (False, False, plc[4]), ['machine_id'])
						continue
					#print(hex(const.DeviceCode.SD.value))

					stCols = ['params_hash', 'programs_hash', 'backup_request']
					stWhe = ['asset_code']
					stPar = (plc[0],)
					currentSate = db.selectWhere(stCols, 'backup_state', stWhe, stPar)

					#print(plc[0])
					#print(str(currentSate))
					#print(plc[2])

					paramHashResponse = plcReadMultipleWord(s, 'E60700', const.DeviceCode.SD.value, 2, 50)
					progHashResponse = plcReadMultipleWord(s, 'E80700', const.DeviceCode.SD.value, 2, 50)

					currentParamHash = '00000000'
					currentProgramHash = '00000000'

					if paramHashResponse[9] + paramHashResponse[10] + progHashResponse[9] + progHashResponse[10] == 0 \
						and len(paramHashResponse) == 15 and len(progHashResponse) == 15:
						#print(paramHashResponse[11])
						currentParamHash = byteArrayToHexString(paramHashResponse[11:15])
						currentProgramHash = byteArrayToHexString(progHashResponse[11:15])

						current_dateTime = datetime.datetime.now()
						updateTime = current_dateTime.strftime("%Y-%m-%d %H:%M:%S")

						if len(currentSate) == 1:
							print(currentSate)
							print(currentParamHash)
							print(currentProgramHash)
							if currentParamHash != currentSate[0][0]:
								updCol = ['params_hash', 'params_change_time', 'backup_request']
								updWhe = ['machine_id']
								updVals = (currentParamHash, updateTime, True, plc[4])
								db.updateValues(updCol, 'backup_state', updVals, updWhe)
							if currentProgramHash != currentSate[0][1]:
								updCol = ['programs_hash', 'programs_change_time', 'backup_request']
								updWhe = ['machine_id']
								updVals = (currentProgramHash, updateTime, True, plc[4])
								db.updateValues(updCol, 'backup_state', updVals, updWhe)
								#print(db._buildUpdateSatement(updCol, 'backup_state', updWhe))
						else:
							insCol = ['machine_id', 'asset_code', 'params_hash', 'programs_hash', 'params_change_time', 'programs_change_time', 'backup_request']
							insVals = (plc[4], plc[0], currentParamHash, currentProgramHash, updateTime, updateTime, True)
							db.insertValues(insCol, 'backup_state', insVals)

							#print(currentParamHash)
							#print(currentProgramHash)
					else:
						#here goes logic when reading either hash returns error. log in db and maybe show plc as disconnected??
						pass

					#print(currentParamHash)
					#print(currentProgramHash)
					#print(db._buildInsertSatement(['params_hash', 'programs_hash'], 'backup_state'))
					#db.insertValues()
			else:
				#must update backupassets here to show connected as false
				db.updateValues(['connected'], '"BackupAssets"', (False, plc[4]), ['machine_id'])
				#continue
		
		print('starting 5 sec sleep')
		time.sleep(5)
		print('finish 5 sec sleep')
		allPlcs = db.selectWhere(cols, '"BackupAssets"', wh, (True,))
		for plc in allPlcs:
			if plc[5]:
				stateCols = ['backup_request']
				stateWhe = ['machine_id']
				statePar = (plc[4],)
				plcState = db.selectWhere(stateCols, 'backup_state', stateWhe, statePar)
				if len(plcState) == 1:
					#print(plcState[0][0])
					if plcState[0][0]:
						log_info('starting backup of ' + plc[0] + ' (' + plc[2] + ')', db)
						try:
							readAllFiles(plc[2], plc[3], 50, plc[1])
							log_info('finished backup of ' + plc[0] + ' (' + plc[2] + ')', db)
							updCol = ['backup_request']
							updWhe = ['machine_id']
							updVals = (False, plc[4])
							db.updateValues(updCol, 'backup_state', updVals, updWhe)
						except Exception as e:
							log_exception('backupProcess - ' + plc[0] + ' - ' + plc[2] + ' - ' + str(e) + ' - PLC will now be disabled. fix' \
							' error before anabling again' , db)
							db.updateValues(['"Enabled"', 'connected'], '"BackupAssets"', (False, False, plc[4]), ['machine_id'])
				else:
					#shouw alyas return one row. what to do when it doesnt??
					pass
		
		print('finished backup process')
		#print(str(allPlcs))


def startup():
	# Create and configure logger
	current_dateTime = datetime.datetime.now()
	updateTime = current_dateTime.strftime("%Y-%m-%d %H%M%S")
	logging.basicConfig(
		level=logging.DEBUG,  # Set the threshold level for logging
		format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Define log message format
		filename='E:/pythonProjects/automatedBackups/logs/' + updateTime +'_proccess.log',  # Specify the log file
		filemode='a'  # 'w' to overwrite the file each time, 'a' to append
	)


def log_debug(msg, dbc : dbConnector.dbConnector):
	logger = logging.getLogger('proccess')
	logger.debug(msg)
	dbc.insert_log('DEBUG', msg)
	#current_dateTime = datetime.datetime.now()
	#updateTime = current_dateTime.strftime("%Y-%m-%d %H:%M:%S")
	#dbc.insertValues(['log_id', 'date_entered', 'level', 'message'], 'backup_log', ('nextval("BackupAssets_machine_id_seq")', updateTime, 'DEBUG', msg))

def log_info(msg, dbc : dbConnector.dbConnector):
	logger = logging.getLogger('proccess')
	logger.info(msg)
	dbc.insert_log('INFO', msg)
	#current_dateTime = datetime.datetime.now()
	#updateTime = current_dateTime.strftime("%Y-%m-%d %H:%M:%S")
	#dbc.insertValues(['log_id', 'date_entered', 'level', 'message'], 'backup_log', ('nextval("BackupAssets_machine_id_seq")', updateTime, 'INFO', msg))

def log_info_nodb(msg):
	logger = logging.getLogger('proccess')
	logger.info(msg)
	#dbc.insert_log('INFO', msg)

def log_exception(msg, dbc : dbConnector.dbConnector):
	logger = logging.getLogger('proccess')
	logger.exception(msg)
	dbc.insert_log('EXCEPTION', msg)

def log_exception_nodb(msg):
	logger = logging.getLogger('proccess')
	logger.exception(msg)
	#dbc.insert_log('INFO', msg)


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

	#readAllFiles('10.114.40.167', 9010, 25, '803.L1.Module.UCDZY00469')

	startup()
	with dbConnector.dbConnector('10.113.162.55', 5432, 'postgres', 'postgres', 'postgres') as db:
		while True:
			try:
				log_info('backupProcess started', db)
				backupProcess()
				log_info('backupProcess finished', db)
				time.sleep(300)
			except Exception as e:
				log_exception(str(e), db)
			finally:
				time.sleep(300)



	#jstr = '202_稼働ﾓﾆﾀ'
	#print(jstr)
	#utf8_bytes = jstr.encode('utf-16') # Encode the string to bytes using utf-16
	#utf8_string = utf8_bytes.decode('utf-16').encode('utf-8').decode('utf-8') # Decode utf-16 and encode to utf-8
	#print(utf8_string)
	
	#testByteArray = 'hello'.encode('utf-16-le')
	#print(testByteArray)
	#hexValues = [f'{byte:02X}' for byte in testByteArray]
	#print(hexValues)