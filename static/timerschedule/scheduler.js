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
