const deleteBtn = document.getElementById('delete-venue');
deleteBtn.onclick = function (e) {
    const venueId = e.target.dataset['id'];
    fetch('/venues/' + venueId, {
        method: 'DELETE'
    }).then(function (response) {
        return response.json();
    }).then(function (jsonResponse) {
        if(jsonResponse['success']) {
            console.log(jsonResponse['success']);
            document.location.href="/venues";
        } else {
            console.log(jsonResponse['success']);
        }
    }).catch(function() {
        console.log('Error');
    });
}