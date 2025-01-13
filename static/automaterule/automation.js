document.addEventListener("DOMContentLoaded", function () {
    // DOM Elements
    const sensorSelect = document.getElementById("sensor-select");
    const relaySelect = document.getElementById("relay-select");
    const thresholdGroup = document.getElementById("threshold-group");
    const conditionSelect = document.getElementById("condition"); // Add condition select element
    const ruleForm = document.getElementById("rule-form");

    async function fetchCategorizedSensors() {
        const response = await fetch('/automation/sensors');
        if (!response.ok) {
            throw new Error(`Failed to load sensors: ${response.statusText}`);
        }
        return await response.json();
    }

    function populateSensorDropdown(selectElement, categorizedSensors, filterFn = () => true) {
        selectElement.innerHTML = '';
        Object.values(categorizedSensors).forEach(category => {
            category.sensors.filter(filterFn).forEach(sensor => {
                // Only add non-relay sensors to the sensor select dropdown
                if (sensor.sensor_key !== "relay") {
                    const option = document.createElement("option");
                    option.value = sensor.sensor_type_id; // Use sensor_type_id for non-relays
                    option.textContent = `${sensor.sensor_id} - ${sensor.sensor_key} (${category.type_display_name})`;
                    selectElement.appendChild(option);
                }
            });
        });
    }
    
    function populateRelayDropdown(selectElement, categorizedSensors) {
        selectElement.innerHTML = '';
        // Only add relays to the relay select dropdown
        Object.values(categorizedSensors).forEach(category => {
            category.sensors.filter(sensor => sensor.sensor_key === "relay").forEach(sensor => {
                const option = document.createElement("option");
                option.value = sensor.device_id; // Use device_id for relays
                option.textContent = `${sensor.device_id} (${category.type_display_name})`;
                selectElement.appendChild(option);
            });
        });
    }
    
    function updateThresholdField(selectedSensorTypeId, categorizedSensors) {
        thresholdGroup.innerHTML = ''; // Clear the threshold field
    
        // Find the sensor category that matches the selected sensor_type_id
        const sensorCategory = Object.values(categorizedSensors).find(category =>
            category.sensors.some(sensor => sensor.sensor_type_id === parseInt(selectedSensorTypeId))
        );
    
        if (sensorCategory) {
            const selectedSensor = sensorCategory.sensors.find(sensor => sensor.sensor_type_id === parseInt(selectedSensorTypeId));
    
            // Check if the sensor has predefined states
            if (sensorCategory.states && Array.isArray(sensorCategory.states) && sensorCategory.states.length > 0) {
                // Predefined states detected; update threshold as dropdown
                conditionSelect.value = "EQUALS";
                conditionSelect.disabled = true; // Disable other conditions
    
                thresholdGroup.innerHTML = `
                    <label for="threshold">State:</label>
                    <select id="threshold" class="form-control" required>
                        ${sensorCategory.states.map(state => `<option value="${state}">${state}</option>`).join('')}
                    </select>`;
            } else {
                // No predefined states; fall back to numeric threshold
                conditionSelect.value = "greater_than"; // Default condition
                conditionSelect.disabled = false; // Enable conditions
    
                thresholdGroup.innerHTML = `
                    <label for="threshold">Threshold (${sensorCategory.unit || ''}):</label>
                    <input type="text" id="threshold" class="form-control" required>`;
            }
        } else {
            // Fallback if no matching category or sensor is found
            thresholdGroup.innerHTML = `
                <label for="threshold">Threshold:</label>
                <input type="text" id="threshold" class="form-control" required>`;
        }
    }
    
    function handleFormSubmit(event) {  
        event.preventDefault();  
    
        // Get selected sensor details  
        const selectedSensorOption = sensorSelect.options[sensorSelect.selectedIndex];  
        const isRelay = relaySelect.value === selectedSensorOption.value;  
        const sensorDetails = selectedSensorOption.textContent.split(' - ');  
    
        // Gather form data  
        const formData = {  
            sensor_id: isRelay ? sensorDetails[0] : sensorDetails[0].trim(),  
            sensor_type_id: isRelay ? null : sensorSelect.value,  
            condition: conditionSelect.value,  
            threshold: document.getElementById("threshold").value,  
            relay_device_id: relaySelect.value,  
            action: document.getElementById("action").value,  
            enabled: document.getElementById("enabled").checked,  
            auto_title: document.getElementById("auto-title").value,  
            auto_description: document.getElementById("auto-description").value  
        };  
    
        // Display formatted JSON  
        console.log(JSON.stringify({  
            method: 'POST',  
            headers: {  
                'Content-Type': 'application/json',  
            },  
            body: formData  
        }, null, 2));  

        fetch('/automation/rule/add', {  
            method: 'POST',  
            headers: {  
                'Content-Type': 'application/json'  
            },  
            body: JSON.stringify(formData)  
        })  
        .then(response => response.json())  
        .then(data => {  
            console.log('Success:', data);  
            alert('Automation rule added successfully!');  
        })  
        .catch(error => {  
            console.error('Error:', error);  
            alert('Failed to add automation rule. Check console for details.');  
        });  
    }
    
    async function initialize() {
        try {
            const categorizedSensors = await fetchCategorizedSensors();
    
            // Initialize sensors (exclude relays from this dropdown)
            populateSensorDropdown(sensorSelect, categorizedSensors);
    
            // Initialize relays (only include relays here)
            populateRelayDropdown(relaySelect, categorizedSensors);
    
            // Event listener for sensor selection change
            sensorSelect.addEventListener("change", (e) => {
                updateThresholdField(e.target.value, categorizedSensors);
            });
    
            // Event listener for form submission
            ruleForm.addEventListener("submit", handleFormSubmit);
    
        } catch (error) {
            console.error("Initialization error:", error);
            alert("Failed to initialize sensors. Check console for details.");
        }
    }
    
    initialize();
});