<?php
include_once 'common.php';
function settecenable($enable, $channel = 0) {
  global $ip_address, $port, $cmd_set_tec_enable;

	$socket = connect_or_abort($ip_address, $port);

  $arguments = $channel . ";" . $enable;
  $msg = $cmd_set_tec_enable . string_length_bytes($arguments);
  $msg = $msg . $arguments;

  socket_write_all($socket, $msg);
	$response_string = socket_read_all($socket);
  socket_close($socket);

	$result_code = extract_result_code_from_response($response_string);

	return $result_code;
}
?>
