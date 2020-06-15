var acc = document.getElementsByClassName("accordion");
var i;

for (i = 0; i < acc.length; i++) {
  acc[i].addEventListener("click", function() {
    this.classList.toggle("active");
    var children = this.parentNode.childNodes;
    children.forEach(child => {
        if(child.style) {
    		if (child.style.maxHeight) {
        		child.style.maxHeight = null;
       		} else {
	        	child.style.maxHeight = child.scrollHeight + "px";
    	    }
        }
    });
    adjust(this.parentNode, this.style.maxHeight);
  });
}

function adjust(node) {
	if(node.style) {
        node.style.maxHeight = window.innerHeight + "px";
    }
    if(node.parentNode){
    	adjust(node.parentNode);
	}
}