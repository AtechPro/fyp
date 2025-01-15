class RelayTimerManager {  
    constructor() {  
        this.activeTimer = null;  

        // Form elements  
        this.form = document.getElementById('relayConfigForm');  
        this.deviceIdSelect = document.getElementById('deviceId');  
        this.timerDurationInput = document.getElementById('timerDuration');  
        this.timeUnitSelect = document.getElementById('timeUnit');  
        this.timerActionSelect = document.getElementById('timerAction');  
        this.timerDisplay = document.getElementById('timerDisplay');  

        // Bind events  
        this.form.addEventListener('submit', this.startTimer.bind(this));  

        // Fetch available relays on initialization  
        this.fetchAvailableRelays();  
    }  

    // Fetch available relays from backend  
    fetchAvailableRelays() {  
        fetch('/timer/relays', {  
            method: 'GET',  
            headers: {  
                'Content-Type': 'application/json'  
            }  
        })  
        .then(response => {  
            if (!response.ok) {  
                throw new Error('Failed to fetch relays');  
            }  
            return response.json();  
        })  
        .then(relays => {  
            // Clear existing options  
            this.deviceIdSelect.innerHTML = '<option value="">Select Device ID</option>';  
            
            // Populate device ID dropdown  
            Object.keys(relays).forEach(deviceId => {  
                const option = document.createElement('option');  
                option.value = deviceId; // Use the device ID as the value  
                option.textContent = `${deviceId} - State: ${relays[deviceId].relay_state}`; // Display state  
                this.deviceIdSelect.appendChild(option);  
            });  
        })  
        .catch(error => {  
            console.error('Error fetching relays:', error);  
            alert('Failed to load available relays');  
        });  
    }  

    startTimer(e) {  
        e.preventDefault();  

        // Validate inputs  
        const deviceId = this.deviceIdSelect.value;  
        const duration = parseInt(this.timerDurationInput.value, 10);  
        const timeUnit = this.timeUnitSelect.value;  
        const timerAction = this.timerActionSelect.value;  

        if (!deviceId || isNaN(duration) || duration <= 0) {  
            alert('Please fill in all fields correctly');  
            return;  
        }  

        // Calculate total seconds  
        let totalSeconds = timeUnit === 'minutes' ? duration * 60 : duration;  

        // Start countdown  
        this.timerDisplay.textContent = `${duration} ${timeUnit}`;  
        this.activeTimer = {  
            remainingTime: totalSeconds,  
            interval: setInterval(() => {  
                this.updateTimer(deviceId, timerAction);  
            }, 1000)  
        };  
    }  

    updateTimer(deviceId, action) {  
        if (!this.activeTimer) return;  

        this.activeTimer.remainingTime--;  

        // Update timer display  
        const minutes = Math.floor(this.activeTimer.remainingTime / 60);  
        const seconds = this.activeTimer.remainingTime % 60;  
        this.timerDisplay.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;  

        // Timer completed  
        if (this.activeTimer.remainingTime <= 0) {  
            this.controlRelay(deviceId, action);  
            this.stopTimer();  
        }  
    }  

    stopTimer() {  
        if (this.activeTimer) {  
            clearInterval(this.activeTimer.interval);  
            this.activeTimer = null;  
            this.timerDisplay.textContent = '00:00';  
        }  
    }  

    controlRelay(deviceId, action) {  
        // Control relay via backend  
        fetch(`/timer/relay/${deviceId}`, {  
            method: 'POST',  
            headers: {  
                'Content-Type': 'application/json'  
            },  
            body: JSON.stringify({ state: action })  
        })  
        .then(response => {  
            if (!response.ok) {  
                throw new Error('Failed to control relay');  
            }  
            return response.json();  
        })  
        .then(data => {  
            console.log(data);  
            alert(`Relay ${deviceId} turned ${action}`);  
        })  
        .catch(error => {  
            console.error('Error:', error);  
            alert(`Failed to control relay ${deviceId}`);  
        });  
    }  
}  

// Initialize the manager when the DOM is fully loaded  
document.addEventListener('DOMContentLoaded', () => {  
    window.relayManager = new RelayTimerManager();  
});