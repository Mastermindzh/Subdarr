#!/bin/bash

# Transform array to json
# Usage: get_json "$(declare -p temperatures)"
# Optional second param for json name: get_json "$(declare -p temperatures)"
get_json(){
	if [ -z "$2" ]; then
		func_output="{"
	else
		func_output="{\"$2\":{"
	fi
	
	eval "declare -A assoc_array="${1#*=}
	
	for i in "${!assoc_array[@]}"
	do
		func_output="$func_output \"$i\":\"${assoc_array[$i]}\","
	done
	func_output=$(echo "$func_output" | sed 's/,$//')

	if [ -z "$2" ]; then
	    func_output="$func_output }"
	else
	    func_output="$func_output }}"
	fi

	echo "$func_output"
}

# map env variables (+ languages) into json
declare -A info

# check for languages
if [ -z "$1" ]; then
	info[languages]='eng'
else
	info[languages]=$1
fi

# check for IP
if [ -z "$2" ]; then
	url="http://localhost:5500"
else
	url=$2
fi

# add /download to the url
url="${url}/download"

if [[ -z "${sonarr_eventtype}" ]]; then
	# if radarr
	info['event_type']=$radarr_eventtype
	info['is_upgrade']="False"
	info['title']=$radarr_movie_title
	info['series_path']=$radarr_movie_path
	info['path_relative']=$radarr_moviefile_relativepath
	info['path']=$radarr_moviefile_path
else
	info['event_type']=$sonarr_eventtype
	info['is_upgrade']=$sonarr_isupgrade
	info['title']=$sonarr_series_title
	info['series_path']=$sonarr_series_path
	info['path_relative']=$sonarr_episodefile_relativepath
	info['path']=$sonarr_episodefile_path
fi

json="$(get_json "$(declare -p info)")"

# call endpoint with data
curl -i \
-H "Accept: application/json" \
-H "Content-Type:application/json" \
-X POST --data "$json" "$url"

