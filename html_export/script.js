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
    adjust(this.parentNode);
  });
}

var bExpand = document.getElementsByClassName("option expandable")[0];
var bCollaps = document.getElementsByClassName("option collapsible")[0];

bExpand.addEventListener("click", function() {
	var accNonActive = Array.prototype.filter.call(acc, function(elem, i, acc) {
		return !elem.className.includes("active");
	});
	for (i = accNonActive.length - 1; i >= 0; i--) {
		accNonActive[i].click();
	}
});

bCollaps.addEventListener("click", function() {
	var accActive = Array.prototype.filter.call(acc, function(elem, i, acc) {
		return elem.className.includes("active");
	});
	for (i = accActive.length - 1; i >= 0; i--) {
		accActive[i].click();
	}
});

function adjust(node) {
	if(node.style) {
        node.style.maxHeight = 10 * window.innerHeight + "px";
    }
    if(node.parentNode){
    	adjust(node.parentNode);
	}
}

