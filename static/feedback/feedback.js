document.addEventListener('DOMContentLoaded', function () {
    const feedbackForm = document.getElementById('feedback-form');
    const feedbackList = document.getElementById('feedback-items');

    // Load feedbacks when the page loads
    loadFeedbacks();

    // Handle feedback submission
    if (feedbackForm) {
        feedbackForm.addEventListener('submit', function (event) {
            event.preventDefault();
            const feedbackTitle = document.getElementById('feedback_title').value.trim();
            const feedbackDesc = document.getElementById('feedback_desc').value.trim();

            if (feedbackTitle && feedbackDesc) {
                fetch('/feedbacks', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        feedback_title: feedbackTitle,
                        feedback_desc: feedbackDesc,
                    }),
                })
                .then(response => response.json())
                .then(data => {
                    if (data.message) {
                        alert(data.message);
                        loadFeedbacks(); // Reload feedbacks after submission
                        feedbackForm.reset(); // Clear the form
                    } else if (data.error) {
                        alert(data.error);
                    }
                })
                .catch(error => console.error('Error:', error));
            } else {
                alert('Both title and description are required.');
            }
        });
    }

    // Function to load feedbacks
    function loadFeedbacks() {
        fetch('/feedbacks')
            .then(response => response.json())
            .then(feedbacks => {
                feedbackList.innerHTML = ''; // Clear existing feedbacks
                if (feedbacks.length === 0) {
                    feedbackList.innerHTML = '<p>No feedback available yet. Submit the first one!</p>';
                } else {
                    feedbacks.forEach(feedback => {
                        const feedbackItem = document.createElement('div');
                        feedbackItem.className = 'feedback-item';
                        feedbackItem.innerHTML = `
                            <h3>${feedback.feedback_title}</h3>
                            <p>${feedback.feedback_desc}</p>
                            ${currentUserRole === 1 ? `<p>User ID: ${feedback.userid}</p>` : ''}
                            <button onclick="editFeedback(${feedback.feedback_id})">Edit</button>
                            <button onclick="deleteFeedback(${feedback.feedback_id})">Delete</button>
                        `;
                        feedbackList.appendChild(feedbackItem);
                    });
                }
            })
            .catch(error => console.error('Error:', error));
    }

    // Function to edit feedback
    window.editFeedback = function (feedbackId) {
        const newTitle = prompt('Enter new title:');
        const newDesc = prompt('Enter new description:');

        if (newTitle && newDesc) {
            fetch(`/feedbacks/${feedbackId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    feedback_title: newTitle,
                    feedback_desc: newDesc,
                }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.message) {
                    alert(data.message);
                    loadFeedbacks(); // Reload feedbacks after edit
                } else if (data.error) {
                    alert(data.error);
                }
            })
            .catch(error => console.error('Error:', error));
        }
    };

    // Function to delete feedback
    window.deleteFeedback = function (feedbackId) {
        if (confirm('Are you sure you want to delete this feedback?')) {
            fetch(`/feedbacks/${feedbackId}`, {
                method: 'DELETE',
            })
            .then(response => response.json())
            .then(data => {
                if (data.message) {
                    alert(data.message);
                    loadFeedbacks(); // Reload feedbacks after deletion
                } else if (data.error) {
                    alert(data.error);
                }
            })
            .catch(error => console.error('Error:', error));
        }
    };
});
