document.addEventListener('DOMContentLoaded', () => {
    const userTableBody = document.getElementById('userTableBody');
    const addUserForm = document.getElementById('addUserForm');

    // Function to load users and populate the table
    function loadUsers() {
        fetch('/userslists')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    const users = data.users;

                    // Clear existing table rows
                    userTableBody.innerHTML = '';

                    // Populate table with users
                    users.forEach(user => {
                        const row = document.createElement('tr');

                        row.innerHTML = `
                            <td>${user.userid}</td>
                            <td>${user.username}</td>
                            <td>${user.name}</td>
                            <td>${user.role === 1 ? 'Admin' : 'User'}</td>
                            <td>
                                <button class="edit-btn" data-id="${user.userid}">
                                    <i class="fas fa-edit"></i> Edit
                                </button>
                                <button class="delete-btn" data-id="${user.userid}">
                                    <i class="fas fa-trash"></i> Delete
                                </button>
                            </td>
                        `;
                        userTableBody.appendChild(row);
                    });

                    // Attach event listeners to the new buttons
                    attachEventListeners();
                } else {
                    alert(data.message);
                }
            })
            .catch(error => {
                console.error('Error fetching users:', error);
            });
    }

    // Attach event listeners to the buttons
    function attachEventListeners() {
        // Handle delete buttons
        const deleteButtons = document.querySelectorAll('.delete-btn');
        deleteButtons.forEach(button => {
            button.addEventListener('click', () => {
                const userId = button.getAttribute('data-id');
                if (confirm('Are you sure you want to delete this user?')) {
                    fetch(`/users/delete/${userId}`, {
                        method: 'DELETE',
                    })
                        .then(response => response.json())
                        .then(data => {
                            if (data.status === 'success') {
                                alert(data.message);
                                loadUsers(); // Reload users after deletion
                            } else {
                                alert(data.message);
                            }
                        })
                        .catch(error => {
                            console.error('Error deleting user:', error);
                        });
                }
            });
        });
    }

    // Handle form submission for adding a new user
    addUserForm.addEventListener('submit', (event) => {
        event.preventDefault();
        const formData = new FormData(addUserForm);
        const data = Object.fromEntries(formData);

        fetch('/users/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    alert(data.message);
                    addUserForm.reset(); // Reset the form
                    loadUsers(); // Reload users after addition
                } else {
                    alert(data.message);
                }
            })
            .catch(error => {
                console.error('Error adding user:', error);
            });
    });

    // Initial load of users
    loadUsers();
});
