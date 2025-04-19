#!/bin/bash

# Define the base URL for the Boxing API
BASE_URL="http://localhost:5000/api"

# Flag to control whether to echo JSON output
ECHO_JSON=false

# Parse command-line arguments
while [ "$#" -gt 0 ]; do
  case $1 in
    --echo-json) ECHO_JSON=true ;;
    *) echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done


###############################################
#
# Health checks
#
###############################################

# Function to check the health of the service
check_health() {
  echo "Checking health status..."
  curl -s -X GET "$BASE_URL/health" | grep -q '"status": "success"'
  if [ $? -eq 0 ]; then
    echo "Service is healthy."
  else
    echo "Health check failed."
    exit 1
  fi
}

# Function to check the database connection
check_db() {
  echo "Checking database connection..."
  curl -s -X GET "$BASE_URL/db-check" | grep -q '"status": "success"'
  if [ $? -eq 0 ]; then
    echo "Database connection is healthy."
  else
    echo "Database check failed."
    exit 1
  fi
}


##########################################################
#
# Boxer Management
#
##########################################################

create_boxer() {
  name=$1
  weight=$2
  height=$3
  reach=$4
  age=$5

  echo "Adding boxer ($name) to the system..."
  response=$(curl -s -X POST "$BASE_URL/create-boxer" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"$name\", \"weight\":$weight, \"height\":$height, \"reach\":$reach, \"age\":$age}")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Boxer added successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Boxer JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to add boxer."
    exit 1
  fi
}

delete_boxer_by_id() {
  boxer_id=$1

  echo "Deleting boxer by ID ($boxer_id)..."
  response=$(curl -s -X DELETE "$BASE_URL/delete-boxer/$boxer_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Boxer deleted successfully by ID ($boxer_id)."
  else
    echo "Failed to delete boxer by ID ($boxer_id)."
    exit 1
  fi
}

get_boxer_by_id() {
  boxer_id=$1

  echo "Getting boxer by ID ($boxer_id)..."
  response=$(curl -s -X GET "$BASE_URL/get-boxer-by-id/$boxer_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Boxer retrieved successfully by ID ($boxer_id)."
    if [ "$ECHO_JSON" = true ]; then
      echo "Boxer JSON (ID $boxer_id):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get boxer by ID ($boxer_id)."
    exit 1
  fi
}

get_boxer_by_name() {
  boxer_name=$1

  echo "Getting boxer by name ($boxer_name)..."
  response=$(curl -s -X GET "$BASE_URL/get-boxer-by-name/$boxer_name")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Boxer retrieved successfully by name ($boxer_name)."
    if [ "$ECHO_JSON" = true ]; then
      echo "Boxer JSON (Name $boxer_name):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get boxer by name ($boxer_name)."
    exit 1
  fi
}

update_boxer_stats() {
  boxer_id=$1
  result=$2

  echo "Updating stats for boxer ($boxer_id) with result ($result)..."
  response=$(curl -s -X POST "$BASE_URL/update-boxer-stats" \
    -H "Content-Type: application/json" \
    -d "{\"boxer_id\":$boxer_id, \"result\":\"$result\"}")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Boxer stats updated successfully."
  else
    echo "Failed to update boxer stats."
    exit 1
  fi
}


##########################################################
#
# Ring Management
#
##########################################################

enter_ring() {
  boxer_id=$1

  echo "Adding boxer ($boxer_id) to the ring..."
  response=$(curl -s -X POST "$BASE_URL/enter-ring" -H "Content-Type: application/json" -d "{\"boxer_id\":$boxer_id}")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Boxer added to the ring successfully."
  else
    echo "Failed to add boxer to the ring."
    exit 1
  fi
}

start_fight() {
  echo "Starting the fight..."
  response=$(curl -s -X POST "$BASE_URL/start-fight")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Fight started successfully."
  else
    echo "Failed to start the fight."
    exit 1
  fi
}

clear_ring() {
  echo "Clearing the ring..."
  response=$(curl -s -X POST "$BASE_URL/clear-ring")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Ring cleared successfully."
  else
    echo "Failed to clear the ring."
    exit 1
  fi
}

# Function to test adding a valid boxer to the ring
enter_ring_valid_boxer() {
  boxer_id=$1

  echo "Entering ring with valid boxer ID ($boxer_id)..."
  response=$(curl -s -X POST "$BASE_URL/enter-ring" -d "boxer_id=$boxer_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Boxer entered successfully by ID ($boxer_id)."
  else
    echo "Failed to enter ring with boxer ID ($boxer_id)."
    exit 1
  fi
}

# Function to test adding two valid boxers to the ring
enter_ring_two_boxers() {
  boxer_id1=$1
  boxer_id2=$2

  echo "Entering ring with boxers ID ($boxer_id1) and ID ($boxer_id2)..."
  response=$(curl -s -X POST "$BASE_URL/enter-ring" -d "boxer_id=$boxer_id1")
  response=$(curl -s -X POST "$BASE_URL/enter-ring" -d "boxer_id=$boxer_id2")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Two boxers entered successfully by ID ($boxer_id1) and ID ($boxer_id2)."
  else
    echo "Failed to enter ring with boxers ID ($boxer_id1) and ID ($boxer_id2)."
    exit 1
  fi
}

# Function to test adding a boxer when the ring is full
enter_ring_while_full() {
  boxer_id1=$1
  boxer_id2=$2
  boxer_id3=$3

  echo "Entering ring with boxer ID ($boxer_id1) and ID ($boxer_id2), then attempting to add ID ($boxer_id3)..."
  response=$(curl -s -X POST "$BASE_URL/enter-ring" -d "boxer_id=$boxer_id1")
  response=$(curl -s -X POST "$BASE_URL/enter-ring" -d "boxer_id=$boxer_id2")
  response=$(curl -s -X POST "$BASE_URL/enter-ring" -d "boxer_id=$boxer_id3")
  if echo "$response" | grep -q '"status": "error"'; then
    echo "Error expected: Ring is full, cannot add more boxers."
  else
    echo "Ring is not full, boxer ID ($boxer_id3) entered unexpectedly."
    exit 1
  fi
}

# Function to test starting a fight with insufficient boxers
fight_with_insufficient_boxers() {
  boxer_id=$1

  echo "Attempting to start a fight with less than two boxers..."
  response=$(curl -s -X POST "$BASE_URL/start-fight")
  if echo "$response" | grep -q '"status": "error"'; then
    echo "Error: Not enough boxers to start a fight."
  else
    echo "Fight started unexpectedly with insufficient boxers."
    exit 1
  fi
}


# Function to test getting all boxers in the ring
get_boxers() {
  echo "Retrieving boxers from the ring..."
  response=$(curl -s -X GET "$BASE_URL/get-boxers")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Boxers retrieved successfully."
  else
    echo "Failed to retrieve boxers."
    exit 1
  fi
}

# Function to test calculating fighting skill of a boxer
get_fighting_skill() {
  boxer_id=$1

  echo "Getting fighting skill for boxer ID ($boxer_id)..."
  response=$(curl -s -X GET "$BASE_URL/get-fighting-skill?boxer_id=$boxer_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Fighting skill retrieved for boxer ID ($boxer_id)."
  else
    echo "Failed to retrieve fighting skill for boxer ID ($boxer_id)."
    exit 1
  fi
}

# Function to test starting a valid fight between two boxers
fight_valid() {
  boxer_id1=$1
  boxer_id2=$2

  echo "Starting fight between boxer ID ($boxer_id1) and ID ($boxer_id2)..."
  response=$(curl -s -X POST "$BASE_URL/start-fight")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Fight started successfully between boxer ID ($boxer_id1) and ID ($boxer_id2)."
  else
    echo "Failed to start fight between boxer ID ($boxer_id1) and ID ($boxer_id2)."
    exit 1
  fi
}

# Function to test fight with insufficient boxers
fight_insufficient_boxers() {
  boxer_id=$1

  echo "Attempting to start a fight with only one boxer (ID: $boxer_id)..."
  response=$(curl -s -X POST "$BASE_URL/start-fight")
  if echo "$response" | grep -q '"status": "error"'; then
    echo "Error: Not enough boxers to start a fight."
  else
    echo "Unexpectedly started a fight with insufficient boxers."
    exit 1
  fi
}


##########################################################
#
# Run Health and Basic Tests
#
##########################################################

# Health checks
check_health
check_db

# Create boxers
create_boxer "Boxer 1" 180 70 75 30
create_boxer "Boxer 2" 175 68 72 28
create_boxer "Boxer 3" 185 71 76 32

# Get a boxer by ID and name
get_boxer_by_id 1
get_boxer_by_name "Boxer 1"

# Update boxer stats
update_boxer_stats 1 "win"
update_boxer_stats 2 "loss"

# Add boxers to the ring
enter_ring 1
enter_ring 2

# Start fight
start_fight

# Clear ring
clear_ring

# Delete boxers by ID
delete_boxer_by_id 1
delete_boxer_by_id 2
delete_boxer_by_id 3

echo "All smoke tests passed successfully!"
