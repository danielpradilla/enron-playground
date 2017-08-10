var d3bubble = function(){
    var width = 960,
        height = 800,
        padding = 1.5, 
        clusterPadding = 6, 
        maxRadius = 80;
        minRadius = 30;
        valueMultiplier = 50;


    var colorScheme = ["#2185D0","#F2711C","#E03997","#00B5AD","#FBBD08","#6435C9","#B5CC18",
                        "#21BA45","#DB2828","#A333C8","#A5673F","#767676","#1B1C1D"]

    var color = d3.scale.ordinal().range(colorScheme); 

    var clusters = []; 

    var nodeNumber=1;

    var nodes = [];

    var brightness = function(rgb) {
      return rgb.r * 0.299 + rgb.g * 0.587 + rgb.b * 0.114;
    };

    var drawChartJSON = function(path){
      d3.json(path, function(error, data){
        if (error){
            console.log(error);
        } else {
            drawChart(data);
        }
      })
    }


    var prepareNodes = function(data){
      var m = data.length;
      data.forEach(function(p, i){
        p.nodes.forEach(function(d, j){
            dvalue = d.value * valueMultiplier;
            var r = ((dvalue * maxRadius) < minRadius ? minRadius : (dvalue * maxRadius));
            var node = {
                cluster: i,
                radius:  r,
                name: d.name,
                x: Math.cos(i / m * 2 * Math.PI) * 200 + width / 2 + Math.random(),
                y: Math.sin(i / m * 2 * Math.PI) * 200 + height / 2 + Math.random()
            };
            nodes.push(node);
            if (!clusters[i] || (r > clusters[i].radius)) {
                clusters[i] = node;
            }
        })
      })
    }


    var drawChart = function(data){

        prepareNodes(data)

        var force = d3.layout.force()
            .nodes(nodes)
            .size([width, height])
            .gravity(0.02)
            .charge(0)
            .on("tick", tick)
            .start();

        var svg = d3.select("#topic-bubbles").append("svg")
            .attr("width", width)
            .attr("height", height);


        //GROUPS
        var node = svg.selectAll("circle")
            .data(nodes)
            .enter().append("g")
            .call(force.drag)
            .call(mouseEvents);


        function mouseEvents(d) {
          d.on("click", click);
          d.on("mouseover", mouseover);
          d.on("mouseout", mouseout);
        }

        function click(d) {
          $.event.trigger({
                type: "node-click",
                d: d
            });
          return true;
        }

        function mouseover(d){
          node.classed("bubble-hover", function(d2){return d2 == d;})
        }

        function mouseout(d){
          node.classed("bubble-hover", false)
        }

        //CIRCLES
        node.append("circle")
            .style("fill", function (d) {return color(d.cluster);})
            .attr("r", function(d){return d.radius})


        //LABELS
        node.append("text")
            .text(function (d) {return d.name;})
            .attr("dx", function(d){ return (-8 * d.name.length)/2;})
            .attr("dy", ".35em")
            .text(function (d) {return d.name})
            .style("stroke", "none")
            .style("fill", textFill)


        function textFill(d){
            var background = color(d.cluster);
            return brightness(d3.rgb(background)) < 120 ? "#fff" : "#000";
        };




        function tick(e) {
            var jitter = 0.5;
            node.each(cluster(10 * e.alpha * e.alpha))
                .each(collide(jitter))
            //.attr("transform", functon(d) {});
            .attr("transform", function (d) {
                var k = "translate(" + d.x + "," + d.y + ")";
                return k;
            })

        }





        //Clustering and collision functions by Mike Bostok
        //https://bl.ocks.org/mbostock/7881887
        function cluster(alpha) {
            return function (d) {
                var cluster = clusters[d.cluster];
                if (cluster === d) return;
                var x = d.x - cluster.x,
                    y = d.y - cluster.y,
                    l = Math.sqrt(x * x + y * y),
                    r = d.radius + cluster.radius;
                if (l != r) {
                    l = (l - r) / l * alpha;
                    d.x -= x *= l;
                    d.y -= y *= l;
                    cluster.x += x;
                    cluster.y += y;
                }
            };
        }

            // Resolves collisions between d and all other circles.
        function collide(alpha) {
            var quadtree = d3.geom.quadtree(nodes);
            return function (d) {
                var r = d.radius + maxRadius + Math.max(padding, clusterPadding),
                    nx1 = d.x - r,
                    nx2 = d.x + r,
                    ny1 = d.y - r,
                    ny2 = d.y + r;
                quadtree.visit(function (quad, x1, y1, x2, y2) {
                    if (quad.point && (quad.point !== d)) {
                        var x = d.x - quad.point.x,
                            y = d.y - quad.point.y,
                            l = Math.sqrt(x * x + y * y),
                            r = d.radius + quad.point.radius + (d.cluster === quad.point.cluster ? padding : clusterPadding);
                        if (l < r) {
                            l = (l - r) / l * alpha;
                            d.x -= x *= l;
                            d.y -= y *= l;
                            quad.point.x += x;
                            quad.point.y += y;
                        }
                    }
                    return x1 > nx2 || x2 < nx1 || y1 > ny2 || y2 < ny1;
                });
            };
        }

    }


    return {
      drawChartJSON: drawChartJSON,
      drawChart: drawChart
    }


}
