export class DashboardManager {
    constructor() {
        this.tiles = [];
        this.tileContainer = null;
        this.initializeDashboard();
        this.loadSavedTiles(); // Future-proof for local storage or database
    }

    initializeDashboard() {
        // Create main dashboard container
        this.tileContainer = document.createElement('div');
        this.tileContainer.classList.add('dashboard-tile-container');
        document.querySelector('.dashboard-container').after(this.tileContainer);

        // Add tile button
        this.createAddTileButton();
    }

    createAddTileButton() {
        // Remove existing add button if any
        const existingButton = this.tileContainer.querySelector('.add-tile-button');
        if (existingButton) existingButton.remove();

        const addButton = document.createElement('button');
        addButton.textContent = '+ Add Tile';
        addButton.classList.add('add-tile-button');
        addButton.addEventListener('click', () => this.showTileCreationModal());
        this.tileContainer.appendChild(addButton);
    }

    showTileCreationModal() {
        // Create modal (same as before)
        const modal = document.createElement('div');
        modal.classList.add('tile-creation-modal');
        modal.innerHTML = `
            <div class="modal-content">
                <h2>Create New Tile</h2>
                <select id="tileType">
                    <option value="temperature">Temperature</option>
                    <option value="humidity">Humidity</option>
                    <option value="custom">Custom Metric</option>
                </select>
                <input type="text" id="tileName" placeholder="Tile Name">
                <div class="modal-actions">
                    <button id="createTileConfirm">Create</button>
                    <button id="createTileCancel">Cancel</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        // Event Listeners
        modal.querySelector('#createTileConfirm').addEventListener('click', () => this.createTile());
        modal.querySelector('#createTileCancel').addEventListener('click', () => document.body.removeChild(modal));
    }

    createTile(type = null, name = null) {
        // Remove modal if it exists
        const existingModal = document.querySelector('.tile-creation-modal');
        if (existingModal) document.body.removeChild(existingModal);

        // Get values from modal or use parameters
        const tileType = type || document.getElementById('tileType').value;
        const tileName = name || document.getElementById('tileName').value || `${tileType.charAt(0).toUpperCase() + tileType.slice(1)} Tile`;

        // Create unique ID for the tile
        const tileId = `tile-${Date.now()}`;

        // Create tile element
        const tile = document.createElement('div');
        tile.classList.add('dashboard-tile', `tile-${tileType}`);
        tile.id = tileId;
        
        // Tile content based on type
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

        // Add remove functionality
        tile.querySelector('.remove-tile').addEventListener('click', (event) => {
            const tileToRemove = document.getElementById(tileId);
            if (tileToRemove) {
                this.tileContainer.removeChild(tileToRemove);
                this.saveTileConfiguration();
            }
        });

        // Add before the add tile button
        const addButton = this.tileContainer.querySelector('.add-tile-button');
        this.tileContainer.insertBefore(tile, addButton);

        // Optional: Save tile configuration
        this.saveTileConfiguration();

        return tile;
    }

    generateTileContent(type) {
        switch(type) {
            case 'temperature':
                return `
                    <canvas id="customTemperatureChart"></canvas>
                    <p>Current: <span id="customTemperatureValue">N/A</span>°C</p>
                `;
            case 'humidity':
                return `
                    <canvas id="customHumidityChart"></canvas>
                    <p>Current: <span id="customHumidityValue">N/A</span>%</p>
                `;
            case 'custom':
                return `
                    <p>Custom metric content goes here</p>
                `;
        }
    }
}

// Initialize dashboard manager
document.addEventListener('DOMContentLoaded', () => {
    window.dashboardManager = new DashboardManager();
});