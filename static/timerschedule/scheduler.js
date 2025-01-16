document.addEventListener('DOMContentLoaded', function () {
    // Fetch relay states when the page loads
    fetchRelayStates();

    // Add event listener for form submission
    document.getElementById('timerForm').addEventListener('submit', function (event) {
        event.preventDefault(); // Prevent the default form submission behavior

        // Gather form data
        const formData = {
            title: document.getElementById('title').value.trim(),
            description: document.getElementById('description').value.trim(),
            trigger_time: document.getElementById('trigger_time').value.trim(),
            days: collectSelectedDays(),
            action: document.getElementById('action').value,
            relay_device_id: document.getElementById('relay_device_id').value.trim(),  // Fetch from dropdown
            enabled: document.getElementById('enabled').checked
        };

        // Validate the form data
        if (!validateFormData(formData)) {
            console.error('Form validation failed. Please fill in all required fields correctly.');
            return;
        }

        // Log the form data before sending
        console.log('Form Data JSON:', JSON.stringify(formData, null, 2));

        // Send a POST request to the server
        fetch('/timer/scheduler', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData) // Send the form data as JSON
        })
        .then(response => response.json()) // Parse the JSON response
        .then(data => {
            // Log the server response
            console.log('Server Response:', data);

            if (data.message) {
                alert('Schedule added successfully!');
            } else {
                alert('Failed to add the schedule. Please try again.');
            }
            // Optionally, reset the form after successful submission
            document.getElementById('timerForm').reset();
        })
        .catch(error => {
            console.error('Error:', error);
            // Optionally, log the error if the request fails
        });
    });
});

// Fetch the relay states and populate the dropdown
function fetchRelayStates() {
    fetch('/timer/relays')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch relay states.');
            }
            return response.json();
        })
        .then(data => {
            populateRelayDropdown(data);
        })
        .catch(error => {
            console.error('Error fetching relay states:', error);
        });
}

// Populate the relay dropdown with data
function populateRelayDropdown(data) {
    const relaySelect = document.getElementById('relay_device_id');
    relaySelect.innerHTML = '<option value="">Select a Relay Device</option>'; // Default option

    if (data && typeof data === 'object' && Object.keys(data).length > 0) {
        for (const deviceId in data) {
            if (data.hasOwnProperty(deviceId)) {
                const option = document.createElement('option');
                option.value = deviceId;
                option.textContent = `Device ID: ${deviceId}, State: ${data[deviceId].relay_state}`;
                relaySelect.appendChild(option);
            }
        }
    } else {
        const noDeviceOption = document.createElement('option');
        noDeviceOption.value = '';
        noDeviceOption.textContent = 'No relay devices available';
        relaySelect.appendChild(noDeviceOption);
    }
}

// Collect selected days from checkboxes
function collectSelectedDays() {
    const selectedDays = [];
    const checkboxes = document.querySelectorAll('input[name="days"]:checked');
    checkboxes.forEach(checkbox => {
        selectedDays.push(checkbox.value); // Add the value of each checked box to the array
    });
    return selectedDays;
}

// Validate form data
function validateFormData(formData) {
    // Ensure title and description are filled
    if (!formData.title || !formData.description) {
        console.error('Validation failed: Title or Description is empty.');
        return false;
    }

    // Ensure trigger_time is valid
    if (!formData.trigger_time) {
        console.error('Validation failed: Trigger Time is empty.');
        return false;
    }

    // Ensure at least one day is selected
    if (!formData.days.length) {
        console.error('Validation failed: No days selected.');
        return false;
    }

    // Ensure action is selected
    if (!formData.action) {
        console.error('Validation failed: No action selected.');
        return false;
    }

    // Ensure relay_device_id is selected (it must not be empty)
    if (!formData.relay_device_id) {
        console.error('Validation failed: No relay device selected.');
        return false;
    }

    // All checks passed
    return true;
}

function fetchTimerList() {
    fetch('/timer/trigger_relay')
        .then(response => response.json())
        .then(data => {
            const timerListDiv = document.getElementById("timerList");
            timerListDiv.innerHTML = ''; // Clear the existing list
            data.triggered_timers.forEach(timer => {
                const timerElement = document.createElement('div');
                timerElement.classList.add('timer-item', 'timer-tile'); // Add 'timer-tile' class

                timerElement.innerHTML = `
                    <div class="timer-content">
                        <h3>${timer.timer.title || `Timer for Device ${timer.timer.relay_device_id}`}:</h3>
                        <p>Status: ${timer.message}</p>
                        <p>Trigger Time: ${timer.timer.trigger_time}</p>
                        <p>Days: ${timer.timer.days}</p>
                        <button class="delete-btn" onclick="deleteTimer(${timer.timer.id})">Delete</button>
                        <button class="edit-btn" onclick="showEditForm(${timer.timer.id})">Edit</button>
                        <div class="edit-form" id="edit-form-${timer.timer.id}" style="display: none;">
                            <label>Title: <input type="text" id="edit-title-${timer.timer.id}" value="${timer.timer.title || ''}"></label>
                            <label>Trigger Time: <input type="time" id="edit-trigger-time-${timer.timer.id}" value="${timer.timer.trigger_time}"></label>
                            <label>Days: <input type="text" id="edit-days-${timer.timer.id}" value="${timer.timer.days}"></label>
                            <label>Action: 
                                <select id="edit-action-${timer.timer.id}">
                                    <option value="ON" ${timer.timer.action === 'ON' ? 'selected' : ''}>ON</option>
                                    <option value="OFF" ${timer.timer.action === 'OFF' ? 'selected' : ''}>OFF</option>
                                </select>
                            </label>
                            <label>Relay Device ID: <input type="text" id="edit-relay-device-id-${timer.timer.id}" value="${timer.timer.relay_device_id}"></label>
                            <button class="save-btn" onclick="editTimer(${timer.timer.id})">Save</button>
                            <button class="cancel-btn" onclick="hideEditForm(${timer.timer.id})">Cancel</button>
                        </div>
                    </div>
                `;
                timerListDiv.appendChild(timerElement);
            });
        })
        .catch(error => console.error('Error fetching timer list:', error));
}

function showEditForm(timerId) {
    document.getElementById(`edit-form-${timerId}`).style.display = 'block';
}

function hideEditForm(timerId) {
    document.getElementById(`edit-form-${timerId}`).style.display = 'none';
}

function editTimer(timerId) {
    const title = document.getElementById(`edit-title-${timerId}`).value;
    const triggerTime = document.getElementById(`edit-trigger-time-${timerId}`).value;
    const days = document.getElementById(`edit-days-${timerId}`).value.split(',');
    const action = document.getElementById(`edit-action-${timerId}`).value;
    const relayDeviceId = document.getElementById(`edit-relay-device-id-${timerId}`).value;

    fetch(`/timer/scheduler/${timerId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            title: title,
            trigger_time: triggerTime,
            days: days,
            action: action,
            relay_device_id: relayDeviceId
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            alert("Timer updated successfully");
            fetchTimerList(); // Refresh the list after editing
        } else {
            alert("Failed to update the timer");
        }
    })
    .catch(error => console.error('Error updating timer:', error));
}


function deleteTimer(timerId) {
    if (!confirm("Are you sure you want to delete this timer?")) {
        return; // Exit if the user cancels the confirmation
    }

    fetch(`/timer/scheduler`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ timer_id: timerId }), // Send the timer_id in the request body
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            alert("Timer deleted successfully");
            fetchTimerList(); // Refresh the list after deleting
        } else {
            alert("Failed to delete the timer");
        }
    })
    .catch(error => console.error('Error deleting timer:', error));
}




// Initial fetch and interval to update the list
setInterval(fetchTimerList, 5000); // Update every 60 seconds
fetchTimerList();
