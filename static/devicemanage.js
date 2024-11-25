document.addEventListener("DOMContentLoaded", function () {
    const deviceForm = document.getElementById("deviceForm");
    const ipAddressInput = document.getElementById("ip-address");
    const statusElement = document.getElementById("status");

    // Function to check device availability via Flask endpoint
    async function checkDeviceAvailability(ip) {
        try {
            const response = await fetch('/mqtt/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ ip: ip })
            });

            const data = await response.json();
            if (data.message === "Subscribed to all topics under 'home/#'") {
                return true;
            }
            return false;
        } catch (error) {
            console.error('Error:', error);
            return false;
        }
    }

    // Event listener for form submission
    deviceForm.addEventListener("submit", async function (event) {
        event.preventDefault();
        const ipAddress = ipAddressInput.value.trim();
        if (ipAddress) {
            statusElement.textContent = "Checking device availability...";

            const isAvailable = await checkDeviceAvailability(ipAddress);

            if (isAvailable) {
                statusElement.textContent = `Device with IP ${ipAddress} is online.`;
                statusElement.style.color = "green";
            } else {
                statusElement.textContent = `Device with IP ${ipAddress} is not reachable.`;
                statusElement.style.color = "red";
            }
        } else {
            statusElement.textContent = "Please enter an IP address.";
            statusElement.style.color = "orange";
        }
    });

    // Check the availability for each device on page load
    const devices = document.querySelectorAll('.device-status');
    devices.forEach(async (device) => {
        const ip = device.id.replace('status-', '');
        const isAvailable = await checkDeviceAvailability(ip);
        if (isAvailable) {
            device.textContent = "Online";
            device.style.color = "green";
        } else {
            device.textContent = "Offline";
            device.style.color = "red";
        }
    });
});
