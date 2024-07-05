(function() {

    const panels = [ 'new', 'inbox', 'sent' ]

    window.changePanel = function(panel, data) {
	for (_panel of panels) {
	    document.querySelector('#'+_panel).style = (panel !== _panel ? 'display: none' : '')
	    document.querySelector('#item-'+_panel).className = (panel !== _panel ? 'menu-item' : 'menu-item selected')
	}
	if (data) {
	    document.querySelector('#from').value = data['addr_to']
	    document.querySelector('#to').value = data['addr_from']
	    document.querySelector('#object').value = 'Re: ' + data['subject']
	    document.querySelector('#contents').value = ''
	}
    }

    window.logout = function() {
	document.cookie = "ph_session=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;"
	window.location = '/'
    }

    document.addEventListener("DOMContentLoaded", (event) => {
	changePanel('inbox')
	setInterval(poll, 5000)
    })

    window.closeModal = function() {
	document.querySelector('#modal').style = 'display: none'
    }

    window.reply = function() {
	closeModal()
	changePanel('new', window.currentMessage)
    }
    
    window.openModal = function(id) {
	read(id)
	if (!inbox) {
	    inbox = []
	}
	if (!sent) {
	    sent = []
	}
	for (msg of inbox) {
	    if (msg.id == id) {
		window.currentMessage = msg
		document.querySelector('#mail-to').innerText = msg.addr_to
		document.querySelector('#mail-from').innerText = msg.addr_from
		document.querySelector('#mail-object').innerText = msg.subject
		document.querySelector('#mail-contents').innerHTML = msg.contents
		document.querySelector('#modal').style = 'display: flex'
	    }
	}
	for (msg of sent) {
	    if (msg.id == id) {
		window.currentMessage = msg
		document.querySelector('#mail-to').innerText = msg.addr_to
		document.querySelector('#mail-from').innerText = msg.addr_from
		document.querySelector('#mail-object').innerText = msg.subject
		document.querySelector('#mail-contents').innerHTML = msg.contents
		document.querySelector('#modal').style = 'display: flex'
	    }
	}
    }

    function onUpdate(request) {
	response = JSON.parse(request.target.response)
	if (this.readyState == 4 && this.status == 200 && response.length) {
	    window.inbox = response
	    updateBoxes()
	    for (message of response) {
		console.log(message)
	    }
	}
    }

    function read(id) {
	const xhr = new XMLHttpRequest()
	xhr.open("GET", "/read/"+id, true)
	xhr.withCredentials = true;
	xhr.send(null)
    }

    function del(id) {
	const xhr = new XMLHttpRequest()
	xhr.open("GET", "/delete/"+id, true)
	xhr.withCredentials = true;
	xhr.send(null)
	document.querySelector('#modal').style = 'display: none'
	updateBoxes()
    }
    
    function poll() {
	const xhr = new XMLHttpRequest()
	xhr.open("GET", "/updates", true)
	xhr.withCredentials = true
	xhr.setRequestHeader('Cache-Control', 'no-cache, no-store, must-revalidate')
	xhr.onreadystatechange = onUpdate
	xhr.send(null);	
    }

    function updateBoxes() {
	let HTMLContents = ''
	let unread = 0
	for (message of inbox) {
	    HTMLContents += `<div class="mailbox-item ${ message.read ? 'read' : '' }" onclick="openModal(${message.id})">
<b>${message.addr_from}</b>
<div style="display: flex; justify-content: space-between"><p>${message.subject}</p><p>${message.date}</p>
</div></div>`
	    if (!message.read) {
		unread += 1
	    }
	}
	if (unread > 0) {
	    document.title = `🛡️  (${unread}) PhotonMail | Secure e-mail`
	} else {
	    document.title = '🛡️  PhotonMail | Secure e-mail'
	}
	
	document.querySelector('#inbox').innerHTML = HTMLContents
    }

    window.del = del;
    
})();
