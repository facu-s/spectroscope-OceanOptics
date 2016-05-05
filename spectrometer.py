#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
	OceanOptics Spectrometer python client
	
	(C) 2016 Mauro Lacy <mauro@lacy.com.ar>
	
    This is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Pointer.  If not, see <http://www.gnu.org/licenses/>.

"""
__version__ = '0.2'

import socket
from sys import exit
#from time import sleep
import struct

# server address
ip_address = "192.168.2.205"
port = 1865

class Spectrometer(object):
	# command constants
	cmd_set_integration_time = "\x00\x01"
	cmd_get_integration_time = "\x00\x02"
	cmd_set_boxcar_width = "\x00\x03"
	cmd_get_boxcar_width = "\x00\x04"
	cmd_set_scans_to_average = "\x00\x05"
	cmd_get_scans_to_average = "\x00\x06"
	cmd_set_target_url = "\x00\x07"
	cmd_get_target_url = "\x00\x08"
	cmd_get_spectrum = "\x00\x09"
	cmd_get_wavelengths = "\x00\x0A"
	cmd_get_serial_number = "\x00\x0B"
	cmd_get_name = "\x00\x0C"
	cmd_get_version = "\x00\x0D"
	cmd_get_calibration_coefficients_from_buffer = "\x00\x0E"
	cmd_set_calibration_coefficients_to_buffer = "\x00\x0F"
	cmd_get_calibration_coefficients_from_eeprom = "\x00\x10"
	cmd_set_calibration_coefficients_to_eeprom = "\x00\x11"
	cmd_get_pixel_binning_factor = "\x00\x12"
	cmd_set_pixel_binning_factor = "\x00\x13"
	cmd_get_integration_time_minimum = "\x00\x14"
	cmd_get_integration_time_maximum = "\x00\x15"
	cmd_get_intensity_maximum = "\x00\x16"
	cmd_get_electric_dark_correction = "\x00\x17"
	cmd_set_electric_dark_correction = "\x00\x18"
	cmd_set_tec_enable = "\x00\x1A"
	cmd_set_tec_temperature = "\x00\x1B"
	cmd_get_tec_temperature = "\x00\x1C"
	cmd_set_lamp_enable = "\x00\x1D"

	# OceanHandler commands  
	cmd_get_current_status = "\x00\x20"
	cmd_get_current_spectrum = "\x00\x21"
	cmd_set_max_acquisitions = "\x00\x22"
	cmd_get_max_acquisitions = "\x00\x23"
	cmd_set_file_save_mode = "\x00\x24"
	cmd_get_file_save_mode = "\x00\x25"
	cmd_set_file_prefix = "\x00\x26"
	cmd_get_file_prefix = "\x00\x27"
	cmd_set_sequence_type = "\x00\x28"
	cmd_get_sequence_type = "\x00\x29"
	cmd_set_sequence_interval = "\x00\x2A"
	cmd_get_sequence_interval = "\x00\x2B"
	cmd_set_save_directory = "\x00\x2C"
	cmd_get_save_directory = "\x00\x2D"
	cmd_save_spectrum = "\x00\x2E"
	cmd_start_sequence = "\x00\x2F"
	cmd_pause_sequence = "\x00\x30"
	cmd_resume_sequence = "\x00\x31"
	cmd_stop_sequence = "\x00\x32"
	cmd_get_sequence_state = "\x00\x33"
	cmd_get_current_sequence_number = "\x00\x34"
	cmd_set_scope_mode = "\x00\x35"
	cmd_get_scope_mode = "\x00\x36"
	cmd_set_scope_interval = "\x00\x37"
	cmd_get_scope_interval = "\x00\x38"

	# convenience constant for null/no parameters to a command
	no_parameters = "\x00\x00"

	def __init__(self, ip_address, port=port, channel=0):
		# connect timeout
		self.timeout = 10
		# default refresh interval for scope mode
		self.default_scope_interval = 5
		
		self.ip_address = ip_address
		self.port = port
		
		self.channel=channel
		
		self.sock = self._connect_or_abort(ip_address, port)

	def _connect_or_abort(self, ip_address, port):
		sock = socket.create_connection((ip_address, port), timeout=self.timeout)
		if sock is None: 
			print("socket: connect failed.")
			exit(1)
		return sock

	def _string_length_bytes(self, s):
		l = len(s)
		hi = l & 0xFF00
		hi = hi >> 8
		lo = l & 0xFF
		result = chr(hi) + chr(lo)
		return result

	def _socket_write_all(self, buffer):
		buffer_length = len(buffer)
		total_sent = 0
		while (total_sent < buffer_length):
			count = self.sock.send(buffer[total_sent:]) 
			total_sent += count
		if count == None: 
			total_sent = None
		return total_sent

	def _socket_read_all(self):
		response_string = ''
		out = True
		while (out):
			out = self.sock.recv(2048) 
			response_string += str(out, 'utf')
		return response_string

	def _socket_read_n(self, expected_length):
		remaining = expected_length
		response_string = ''
		chunk = True
		while (chunk):
			chunk = self.sock.recv(remaining)
			out = str(chunk, 'utf') 
			response_string += out
			remaining -= len(out)
		return response_string, expected_length - remaining

	def _extract_result_code_from_response(self, response_string):
		result = ord(response_string[0]) * 256 + ord(response_string[1]);
		response_string = response_string[2:]
		return result, response_string
	
	def _close(self):
		self.sock.close()
		self.sock = None
	
	def _build_command(self, cmd, *args):
		msg = bytearray(cmd, 'utf')
		arguments = ''
		if len(args):
			for a in args:
				arguments += str(a) + ';'
			msg += struct.pack('!H', len(arguments));
		else:
			arguments = self.no_parameters
		msg += bytearray(arguments, 'utf');
		return msg
	
	def _send_command(self, cmd, *args):
		if self.sock is None:
			self.sock = self._connect_or_abort(ip_address, port)
		msg = self._build_command(cmd, *args)

		self._socket_write_all(msg)
		
		result = self._socket_read_all()
		
		self._close()
		
		code = 0
		if len(result) >= 2:
			code, result = self._extract_result_code_from_response(result)
		return result if code == 1 else None # FIXME?: what are valid code values?

	def _send_command_n(self, cmd, *args):
		if self.sock is None:
			self.sock = self._connect_or_abort(ip_address, port)

		msg = self._build_command(cmd, *args)

		self._socket_write_all(msg)

		output_string = None

		# we are expecting 2 bytes result code
		out, result = self._socket_read_n(2)
		if result == 2:
			res0 = ord(out[0]) << 8
			res1 = ord(out[1])
			result_code = res0 | res1
			
			# now we are expecting 4 bytes with the result length
			out, result = self._socket_read_n(4)
			if result == 4:
				b0 = ord(out[0]) << 24
				b1 = ord(out[1]) << 16
				b2 = ord(out[2]) << 8
				b3 = ord(out[3])
				result_length = b0 | b1 | b2 | b3
		
				output_string, _ = self._socket_read_n(result_length)
		self._close()
		
		return output_string 

	def get_version(self):
		return self._send_command(self.cmd_get_version)

	def get_serial(self):
		return self._send_command(self.cmd_get_serial_number, self.channel)

	def get_integration(self):
		return self._send_command(self.cmd_get_integration_time, self.channel)
	
	def get_get_boxcar(self):
		return self._send_command(self.cmd_get_boxcar_width, self.channel)
	
	def get_average(self):
		return self._send_command(self.cmd_get_scans_to_average, self.channel)

	def get_target(self):
		return self._send_command(self.cmd_get_target_url)

	def get_spectrum(self):
		return self._send_command_n(self.cmd_get_spectrum, self.channel)

	def get_wavelengths(self):
		return self._send_command_n(self.cmd_get_wavelengths, self.channel)

	def get_name(self):
		return self._send_command(self.cmd_get_name, self.channel)

	def get_calibration_buffer(self):
		return self._send_command_n(self.cmd_get_calibration_coefficients_from_buffer, self.channel)

	def get_calibration_eeprom(self):
		return self._send_command_n(self.cmd_get_calibration_coefficients_from_eeprom, self.channel)

	def get_binning(self):
		return self._send_command(self.cmd_get_pixel_binning_factor, self.channel)

	def get_min_integration(self):
		return self._send_command(self.cmd_get_integration_time_minimum, self.channel)

	def get_max_integration(self):
		return self._send_command(self.cmd_get_integration_time_maximum, self.channel)

	def get_max_intensity(self):
		return self._send_command(self.cmd_get_intensity_maximum, self.channel)

	def get_e_d_correct(self):
		return self._send_command(self.cmd_get_electric_dark_correction, self.channel)

	def get_tec_temperature(self):
		return self._send_command(self.cmd_get_tec_temperature, self.channel)

	def get_current_status(self):
		return self._send_command(self.cmd_get_current_status, self.channel)

	def current_spectrum(self):
		return self._send_command_n(self.cmd_get_current_spectrum)

	def get_max_acquisitions(self):
		return self._send_command(self.cmd_get_max_acquisitions, self.channel)

	def get_save_mode(self):
		return self._send_command(self.cmd_get_file_save_mode, self.channel)

	def get_file_prefix(self):
		return self._send_command(self.cmd_get_file_prefix, self.channel)

	def get_sequence_type(self):
		return self._send_command(self.cmd_get_sequence_type, self.channel)

	def get_sequence_interval(self):
		return self._send_command(self.cmd_get_sequence_interval, self.channel)

	def get_save_location(self):
		return self._send_command(self.cmd_get_save_directory, self.channel)

	def get_sequence_state(self):
		return self._send_command(self.cmd_get_sequence_state, self.channel)

	def get_sequence_number(self):
		return self._send_command(self.cmd_get_current_sequence_number, self.channel)

	def get_scope_mode(self):
		return self._send_command(self.cmd_get_scope_mode, self.channel)

	def get_scope_interval(self):
		return self._send_command(self.cmd_get_scope_interval, self.channel)

	def set_integration_time(self, seconds):
		return self._send_command(self.cmd_set_integration_time, int(seconds*1e6))

if __name__ == '__main__':
	spectrometer = Spectrometer(ip_address, port)
	print('Version:', spectrometer.get_version())
	print('Serial:', spectrometer.get_serial())
	print('Integration time:', spectrometer.get_integration())
	print('Spectrum:', spectrometer.get_spectrum())