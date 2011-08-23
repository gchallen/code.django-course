window.addEvent('domready', function() {
	// Kwick Box
	if ($('kwick-box4')) {
		var kwicks = $$('#kwick .kwick');
		var fx = new Fx.Elements(kwicks, {wait: false, duration: 200, transition: Fx.Transitions.quadOut});
		kwicks.each(function(kwick, i){
			kwick.addEvent('mouseenter', function(e){
				var obj = {};
				obj[i] = {
					'width': [kwick.getStyle('width').toInt(), 480]
				};
				kwicks.each(function(other, j){
					if (other != kwick){
						var w = other.getStyle('width').toInt();
						if (w != 160) obj[j] = {'width': [w, 160]};
					}
				});
				fx.start(obj);
			});
		});
		
	 	$('kwick').addEvent('mouseleave', function(e){
			var obj = {};
			kwicks.each(function(other, j){
				obj[j] = {'width': [other.getStyle('width').toInt(), 240]};
			});
			fx.start(obj);
		});
	}
	if ($('kwick-box5')) {
		var kwicks = $$('#kwick .kwick');
		var fx = new Fx.Elements(kwicks, {wait: false, duration: 200, transition: Fx.Transitions.quadOut});
		kwicks.each(function(kwick, i){
			kwick.addEvent('mouseenter', function(e){
				var obj = {};
				obj[i] = {
					'width': [kwick.getStyle('width').toInt(), 384]
				};
				kwicks.each(function(other, j){
					if (other != kwick){
						var w = other.getStyle('width').toInt();
						if (w != 144) obj[j] = {'width': [w, 144]};
					}
				});
				fx.start(obj);
			});
		});
		
	 	$('kwick').addEvent('mouseleave', function(e){
			var obj = {};
			kwicks.each(function(other, j){
				obj[j] = {'width': [other.getStyle('width').toInt(), 192]};
			});
			fx.start(obj);
		});
	}
});
