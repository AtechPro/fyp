document.addEventListener("DOMContentLoaded", function () {
    // DOM Elements
    const sensorSelect = document.getElementById("sensor-select");
    const relaySelect = document.getElementById("relay-select");
    const thresholdGroup = document.getElementById("threshold-group");
    const conditionSelect = document.getElementById("condition");
    const ruleForm = document.getElementById("rule-form");
    const rulesContainer = document.getElementById("rules-container");

    // Fetch categorized sensors
    async function fetchCategorizedSensors() {
        const response = await fetch('/automation/sensors');
        if (!response.ok) {
            throw new Error(`Failed to load sensors: ${response.statusText}`);
        }
        return await response.json();
    }

    // Populate sensor dropdown
    function populateSensorDropdown(selectElement, categorizedSensors, filterFn = () => true) {
        selectElement.innerHTML = '';
        Object.values(categorizedSensors).forEach(category => {
            category.sensors.filter(filterFn).forEach(sensor => {
                if (sensor.sensor_key !== "relay") {
                    const option = document.createElement("option");
                    option.value = sensor.sensor_type_id;
                    option.textContent = `${sensor.sensor_id} - ${sensor.sensor_key} (${category.type_display_name})`;
                    selectElement.appendChild(option);
                }
            });
        });
    }

    // Populate relay dropdown
    function populateRelayDropdown(selectElement, categorizedSensors) {
        selectElement.innerHTML = '';
        Object.values(categorizedSensors).forEach(category => {
            category.sensors.filter(sensor => sensor.sensor_key === "relay").forEach(sensor => {
                const option = document.createElement("option");
                option.value = sensor.device_id;
                option.textContent = `${sensor.device_id} (${category.type_display_name})`;
                selectElement.appendChild(option);
            });
        });
    }

    // Update threshold field based on selected sensor
    function updateThresholdField(selectedSensorTypeId, categorizedSensors) {
        thresholdGroup.innerHTML = '';
        const sensorCategory = Object.values(categorizedSensors).find(category =>
            category.sensors.some(sensor => sensor.sensor_type_id === parseInt(selectedSensorTypeId))
        );

        if (sensorCategory) {
            if (sensorCategory.states && Array.isArray(sensorCategory.states) && sensorCategory.states.length > 0) {
                conditionSelect.value = "EQUALS";
                conditionSelect.disabled = true;
                thresholdGroup.innerHTML = `
                    <label for="threshold">State:</label>
                    <select id="threshold" class="form-control" required>
                        ${sensorCategory.states.map(state => `<option value="${state}">${state}</option>`).join('')}
                    </select>`;
            } else {
                conditionSelect.value = "greater_than";
                conditionSelect.disabled = false;
                thresholdGroup.innerHTML = `
                    <label for="threshold">Threshold (${sensorCategory.unit || ''}):</label>
                    <input type="text" id="threshold" class="form-control" required>`;
            }
        } else {
            thresholdGroup.innerHTML = `
                <label for="threshold">Threshold:</label>
                <input type="text" id="threshold" class="form-control" required>`;
        }
    }

    // Handle form submission for adding/editing a rule
    function handleFormSubmit(event) {
        event.preventDefault();
        const submitButton = document.querySelector('#rule-form button[type="submit"]');
        const isEditMode = submitButton.textContent === 'Update Rule';
        const ruleId = isEditMode ? submitButton.getAttribute('data-rule-id') : null;

        const selectedSensorOption = sensorSelect.options[sensorSelect.selectedIndex];
        const isRelay = relaySelect.value === selectedSensorOption.value;
        const sensorDetails = selectedSensorOption.textContent.split(' - ');

        const formData = {
            sensor_id: isRelay ? sensorDetails[0] : sensorDetails[0].trim(),
            sensor_type_id: isRelay ? null : sensorSelect.value,
            condition: conditionSelect.value,
            threshold: document.getElementById("threshold").value,
            relay_device_id: relaySelect.value,
            action: document.getElementById("action").value,
            enabled: document.getElementById("enabled").checked,
            auto_title: document.getElementById("auto-title").value,
            auto_description: document.getElementById("auto-description").value,
        };

        const url = isEditMode ? `/automation/rules/${ruleId}` : '/automation/rule/add';
        const method = isEditMode ? 'PUT' : 'POST';

        fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData),
        })
            .then(response => response.json())
            .then(data => {
                console.log('Success:', data);
                alert(isEditMode ? 'Rule updated successfully!' : 'Rule added successfully!');
                resetForm();
                fetchRuleAppliedStatus(); // Refresh the rule list
            })
            .catch(error => {
                console.error('Error:', error);
                alert(`Failed to ${isEditMode ? 'update' : 'add'} rule. Check console for details.`);
            });
    }

    // Reset the form
    function resetForm() {
        ruleForm.reset();
        const submitButton = document.querySelector('#rule-form button[type="submit"]');
        submitButton.textContent = 'Add Rule';
        submitButton.removeAttribute('data-rule-id');
    }

    // Fetch and display rule applied status
    async function fetchRuleAppliedStatus() {
        try {
            const response = await fetch('/automation/sensors/rule_applied');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            displayRuleStatus(data);
        } catch (error) {
            console.error('Error fetching rule applied status:', error);
            rulesContainer.innerHTML = `
                <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
                    Failed to fetch rule applied status: ${error.message}
                </div>`;
        }
    }

    // Display rule status in the UI
    function displayRuleStatus(data) {
        rulesContainer.innerHTML = '';
        Object.entries(data).forEach(([sensorType, sensorData]) => {
            const sensorTypeContainer = document.createElement('div');
            sensorTypeContainer.className = 'mb-6 bg-white shadow-md rounded-lg p-4';

            const sensorTypeHeader = document.createElement('h2');
            sensorTypeHeader.className = 'text-xl font-bold text-gray-800 mb-4 capitalize';
            sensorTypeHeader.textContent = sensorType.replace('_', ' ');
            sensorTypeContainer.appendChild(sensorTypeHeader);

            if (sensorData.sensors && sensorData.sensors.length > 0) {
                const sensorsGrid = document.createElement('div');
                sensorsGrid.className = 'space-y-4';

                sensorData.sensors.forEach(sensor => {
                    const sensorCard = document.createElement('div');
                    sensorCard.className = 'bg-gray-50 rounded-lg p-4 border border-gray-200';

                    if (sensor.rules && sensor.rules.length > 0) {
                        sensor.rules.forEach(rule => {
                            const ruleElement = document.createElement('div');
                            ruleElement.className = `rounded-md ${rule.is_matched ? 'bg-green-50' : 'bg-yellow-50'}`;
                            ruleElement.innerHTML = `
                                <div class="p-4">
                                    <h3 class="text-2xl font-bold text-gray-800 mb-2">${rule.auto_title}</h3>
                                    <p class="text-lg text-gray-700 mb-4">${rule.auto_description}</p>
                                    <div class="text-sm text-gray-600 space-y-1">
                                        <div class="flex justify-between">
                                            <span>Device: ${sensor.device_id} (Last Value: ${sensor.last_value})</span>
                                            <span class="font-medium ${rule.is_matched ? 'text-green-600' : 'text-yellow-600'}">
                                                ${rule.is_matched ? 'Matched' : 'Not Matched'}
                                            </span>
                                        </div>
                                        <div class="flex justify-between">
                                            <span>Condition: ${rule.condition} ${rule.threshold}</span>
                                            <span>Action: ${rule.action}</span>
                                        </div>
                                        <p class="italic text-gray-500">${rule.status_message}</p>
                                    </div>
                                    <div class="mt-4 flex space-x-2">
                                        <button class="edit-rule-button bg-blue-500 text-white px-4 py-2 rounded" data-rule-id="${rule.rule_id}">Edit</button>
                                        <button class="delete-rule-button bg-red-500 text-white px-4 py-2 rounded" data-rule-id="${rule.rule_id}">Delete</button>
                                    </div>
                                </div>`;
                            sensorCard.appendChild(ruleElement);
                        });
                    } else {
                        const noRulesMessage = document.createElement('div');
                        noRulesMessage.className = 'text-center text-gray-500 italic text-sm';
                        noRulesMessage.textContent = 'No rules applied for this sensor';
                        sensorCard.appendChild(noRulesMessage);
                    }

                    sensorsGrid.appendChild(sensorCard);
                });

                sensorTypeContainer.appendChild(sensorsGrid);
            } else {
                const noSensorsMessage = document.createElement('div');
                noSensorsMessage.className = 'text-center text-gray-500 italic';
                noSensorsMessage.textContent = 'No sensors found for this type';
                sensorTypeContainer.appendChild(noSensorsMessage);
            }

            rulesContainer.appendChild(sensorTypeContainer);
        });

        // Add event listeners for edit and delete buttons
        document.querySelectorAll('.edit-rule-button').forEach(button => {
            button.addEventListener('click', (e) => {
                const ruleId = e.target.getAttribute('data-rule-id');
                fetchRuleDetails(ruleId);
            });
        });

        document.querySelectorAll('.delete-rule-button').forEach(button => {
            button.addEventListener('click', (e) => {
                const ruleId = e.target.getAttribute('data-rule-id');
                deleteRule(ruleId);
            });
        });
    }

    // Fetch rule details for editing
    async function fetchRuleDetails(ruleId) {
        try {
            const response = await fetch(`/automation/rules/${ruleId}`);
            if (!response.ok) {
                throw new Error(`Failed to fetch rule details: ${response.statusText}`);
            }
            const rule = await response.json();
            populateFormForEdit(rule);
        } catch (error) {
            console.error('Error fetching rule details:', error);
            alert('Failed to fetch rule details. Check console for details.');
        }
    }

    // Populate the form for editing
    function populateFormForEdit(rule) {
        document.getElementById('sensor-select').value = rule.sensor_type_id || '';
        document.getElementById('relay-select').value = rule.relay_device_id || '';
        document.getElementById('condition').value = rule.condition || '';
        document.getElementById('threshold').value = rule.threshold || '';
        document.getElementById('action').value = rule.action || '';
        document.getElementById('enabled').checked = rule.enabled || false;
        document.getElementById('auto-title').value = rule.auto_title || '';
        document.getElementById('auto-description').value = rule.auto_description || '';

        const submitButton = document.querySelector('#rule-form button[type="submit"]');
        submitButton.textContent = 'Update Rule';
        submitButton.setAttribute('data-rule-id', rule.rule_id);

        document.getElementById('rule-form').scrollIntoView({ behavior: 'smooth' });
    }

    // Delete a rule
    function deleteRule(ruleId) {
        fetch(`/automation/rules/${ruleId}`, {
            method: 'DELETE',
        })
            .then(response => response.json())
            .then(data => {
                console.log('Success:', data);
                alert('Rule deleted successfully!');
                fetchRuleAppliedStatus(); // Refresh the rule list
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to delete rule. Check console for details.');
            });
    }

    // Initialize the page
    async function initialize() {
        try {
            const categorizedSensors = await fetchCategorizedSensors();
            populateSensorDropdown(sensorSelect, categorizedSensors);
            populateRelayDropdown(relaySelect, categorizedSensors);
            sensorSelect.addEventListener("change", (e) => updateThresholdField(e.target.value, categorizedSensors));
            ruleForm.addEventListener("submit", handleFormSubmit);
            fetchRuleAppliedStatus(); // Initial fetch
            setInterval(fetchRuleAppliedStatus, 1000); // Time to Refresh 
        } catch (error) {
            console.error("Initialization error:", error);
            alert("Failed to initialize sensors. Check console for details.");
        }
    }

    initialize();
});