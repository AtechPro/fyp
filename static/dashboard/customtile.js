export class DashboardManager {
    constructor() {
        this.tiles = [];
        this.tileContainer = null;
        this.initializeDashboard();
        this.loadTileConfiguration();
    }

    initializeDashboard() {
        this.tileContainer = document.createElement('div');
        this.tileContainer.classList.add('dashboard-tile-container');
        document.querySelector('.dashboard-container').after(this.tileContainer);
        
        this.addTileCreationButton();
    }

    addTileCreationButton() {
        const addButton = document.createElement('button');
        addButton.classList.add('add-tile-button');
        addButton.textContent = '+ Add Tile';
        addButton.addEventListener('click', () => this.showTileCreationModal());
        this.tileContainer.appendChild(addButton);
    }

    showTileCreationModal() {
        const modal = document.createElement('div');
        modal.classList.add('tile-creation-modal');
        modal.innerHTML = `
            <div class="modal-content">
                <h2>Create New Tile</h2>
                <select id="tileType">
                    ${Object.keys(SENSOR_TYPES).map(type => 
                        `<option value="${type}">${type.charAt(0).toUpperCase() + type.slice(1)}</option>`
                    ).join('')}
                </select>
                <input type="text" id="tileName" placeholder="Tile Name">
                <div class="modal-actions">
                    <button id="createTileConfirm">Create</button>
                    <button id="createTileCancel">Cancel</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        modal.querySelector('#createTileConfirm').addEventListener('click', () => this.createTile());
        modal.querySelector('#createTileCancel').addEventListener('click', () => document.body.removeChild(modal));
    }

    createTile(type = null, name = null) {
        const existingModal = document.querySelector('.tile-creation-modal');
        if (existingModal) document.body.removeChild(existingModal);

        const tileType = type || document.getElementById('tileType').value;
        const tileName = name || document.getElementById('tileName').value || 
                        `${tileType.charAt(0).toUpperCase() + tileType.slice(1)} Tile`;

        if (!SENSOR_TYPES[tileType]) {
            console.error(`Invalid tile type: ${tileType}`);
            return null;
        }

        const tileId = `tile-${Date.now()}`;
        const tile = document.createElement('div');
        tile.classList.add('dashboard-tile', `tile-${tileType}`);
        tile.id = tileId;
        
        tile.innerHTML = `
            <div class="tile-header">
                <h3>${tileName}</h3>
                <div class="tile-actions">
                    <button class="remove-tile" data-tile-id="${tileId}">❌</button>
                </div>
            </div>
            <div class="tile-content">
                ${this.generateTileContent(tileType)}
            </div>
        `;

        tile.querySelector('.remove-tile').addEventListener('click', () => {
            this.tileContainer.removeChild(tile);
            this.saveTileConfiguration();
        });

        const addButton = this.tileContainer.querySelector('.add-tile-button');
        this.tileContainer.insertBefore(tile, addButton);

        this.saveTileConfiguration();
        return tile;
    }

    generateTileContent(type) {
        const sensorConfig = SENSOR_TYPES[type];
        return sensorConfig 
            ? sensorConfig.template(
                `${type}Chart`, 
                `${type}Value`, 
                sensorConfig.unit
            )
            : `<p>Unsupported sensor type: ${type}</p>`;
    }

    saveTileConfiguration() {
        const tileConfigs = Array.from(this.tileContainer.querySelectorAll('.dashboard-tile'))
            .map(tile => ({
                id: tile.id,
                type: tile.classList[1].replace('tile-', ''),
                name: tile.querySelector('.tile-header h3').textContent
            }));
        localStorage.setItem('dashboardTiles', JSON.stringify(tileConfigs));
    }

    loadTileConfiguration() {
        const savedConfigs = JSON.parse(localStorage.getItem('dashboardTiles') || '[]');
        savedConfigs.forEach(config => 
            this.createTile(config.type, config.name)
        );
    }
}

const SENSOR_TYPES = {
    temperature: {
        unit: '°C',
        template: (chartId, valueId, unit) => `
            <canvas id="${chartId}"></canvas>
            <p>Current: <span id="${valueId}">N/A</span>${unit}</p>
        `
    },
    humidity: {
        unit: '%',
        template: (chartId, valueId, unit) => `
            <canvas id="${chartId}"></canvas>
            <p>Current: <span id="${valueId}">N/A</span>${unit}</p>
        `
    },
    custom: {
        unit: '',
        template: () => `<p>Custom metric content goes here</p>`
    },
    photoInterrupter: {
        unit: '',
        template: (statusId) => `
            <p>Status: <span id="${statusId}">N/A</span></p>
        `
    },
    relay: {
        unit: '',
        template: (toggleId) => `
            <button id="${toggleId}">Toggle Relay</button>
            <p>Relay Status: <span id="${toggleId}-status">OFF</span></p>
        `
    },
    reedSwitch: {
        unit: '',
        template: (statusId) => `
            <p>Reed Switch: <span id="${statusId}">N/A</span></p>
        `
    },
    pirSensor: {
        unit: '',
        template: (statusId) => `
            <p>PIR Sensor: Motion <span id="${statusId}">N/A</span></p>
        `
    },
    photoresistor: {
        unit: '',
        template: (valueId) => `
            <p>Light Level: <span id="${valueId}">N/A</span></p>
            <p>Condition: <span id="${valueId}-condition">N/A</span></p>
        `
    }
};


// Initialize dashboard manager
document.addEventListener('DOMContentLoaded', () => {
    window.dashboardManager = new DashboardManager();
});