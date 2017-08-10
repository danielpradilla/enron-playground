var ep = ep || {}

ep.chart = d3bubble()
ep.url = '/gunicorn';

ep.mockTopics = 'data/topics.json';
ep.mockAuthors = 'data/authors.json';


ep.onTopicClick = function(data){

}

ep.fetchTopics = function() {
	const url = ep.url + '/topics';
	return fetch(url)
		.then(response=>response.json())
		.then(data=>data)
}

ep.fetchAuthorsTopics = function(topic){
	const url = `${ep.url}/author_topics?id=${topic}`
	return fetch(url)
		.then(response=>response.json())
		.then(data=>data)
}

ep.fetchDocumentList = function(author) {
	const url = `${ep.url}/get_message_list?id=${author}`
	return fetch(url)
		.then(response=>response.json())
		.then(data => data);
}


ep.fetchDocument = function(id) {
	const url = `${ep.url}/get_message?id=${id}`
	return fetch(url)
		.then(response=>response.json())
		.then(data => data);
}

ep.formatPercent = function(number){
	let rtn = (100*number).toLocaleString(
	  undefined, 
	  { minimumFractionDigits: 2 }
	);
	rtn+='%'
	return rtn;
}




ep.getAuthorCards = function(topic){
	$('#author-cards').dimmer('show')
	ep.fetchAuthorsTopics(topic)
		.then(data=> ep.updateAuthorCards(data, topic))
}

ep.getAuthorCardHTML = function(cards, topic){
	let rtn ='';
	cards.forEach(card=>{
		rtn+=`<div id="${card.from}" class="card">
		        <div class="content">
		          <div class="header">${card.from}</div>
		          <div class="meta">${card.from}</div>
		          <div class="description">
		            Hi! my name is ${card.from} and 
		            I have written <strong>${card.count}</strong> emails. 
		            The probability that you are 
		            looking for me is <strong>${ep.formatPercent(card[topic])}</strong>.
		          </div>
		        </div>
		      </div>`;
	});
	return rtn;

} 

ep.updateAuthorCards = function(data, topic){
	let html = ep.getAuthorCardHTML(data, topic);
	$('#author-cards-container').html(html);
	$('#author-cards').dimmer('hide');
	$("#author-cards-container .card").click(function(evt){
		let id = $(this).attr("id");
		ep.getDocuments(id)
	})
}






ep.getDocuments = function(author){
	$('#author-documents').dimmer('show');
	ep.fetchDocumentList(author)
		.then(ep.updateDocumentList)	
}

ep.getDocumentListHTML = function(list){
	let rtn = `<table class="ui striped selectable table">
				<thead>
					<tr>
					  <th>Date Sent</th>
					  <th>Subject</th>
					</tr>
				</thead>
            	<tbody>
		     `;
	list.forEach(doc=>{
		rtn+=`
	        <tr id="${doc['message-id']}">
	          <td>${doc.date}</td>
	          <td>${doc.subject}</td>
	        </tr>
		`;
	})
	rtn += '</tbody></table>';

	return rtn;
}

ep.updateDocumentList = function(data){
	let html = ep.getDocumentListHTML(data);
	$('#author-documents-container').html(html);
	$('#author-documents').dimmer('hide');
	$('#author-documents-container tbody tr').click(function(evt){
		let id = $(this).attr("id");
		ep.getDocument(id)
	});
}




ep.getDocument = function(id){
	$('#document').dimmer('show');
	ep.fetchDocument(id)
		.then(ep.updateDocument)	
}

ep.getDocumentHTML = function(docs){
	let doc = docs[0];
	return `<h4>${doc['message-id']}</h4>
			<div>${doc.filename}</div>
			<h4>${doc.to}</h4>
			<h3>${doc.subject}</h4>
			<h4>${doc.date}</h4>
			<div>${doc.body}</div>
			`;
}

ep.updateDocument = function(data){
	let html = ep.getDocumentHTML(data);
	$('#document-container').html(html);
	$('#document').dimmer('hide');	
}


ep.addEventListeners = function(){
	$(document).on("node-click", ep.topicClick); //jquery event for a lazy way of communicating with the d3chart

}

ep.topicClick = function(evt){
	let topic = 'topic'+evt.d.cluster; //topicN zero based
	ep.getAuthorCards(topic);
	$('#author-documents-container').html('');
	$('#document-container').html('');
	document.querySelector('#author-cards-title').scrollIntoView({block: "start", behavior: "smooth"}); 
}


ep.onLoad = function(){
	ep.fetchTopics()
	.then(ep.chart.drawChart);
	ep.addEventListeners();
}

