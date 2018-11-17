var d3bubble = function(){
    var width = 960,
        height = 720,
        padding = 1.5, 
        clusterPadding = 6, 
        maxRadius = height/10;
        minRadius = maxRadius*0.3;
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
                description: d.description,
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
            .charge(function(d){return d.radius;})
            .on("tick", tick)
            .start();

        var svg = d3.select("#topic-bubbles").append("svg")
            .attr("width", width)
            .attr("height", height);




        //LEGEND
        var legendContainer = svg.append("g")
                            .attr("transform", "translate(0, 20)")
                            ;

        var legend = legendContainer.selectAll(".legend")
                  .data(data)
                  .enter().append("g")
                  .attr("class", function(d,i) {console.log(d,i); return 'legend cluster' + i;})
                  .attr("dx", width )
                  .attr("transform", function (d, i) { 
                    return "translate(0," + i * 20 + ")"; 
                  })
                            .on("mouseover", legendMouseover)
          .on("mouseout", legendMouseout)
;

        legend.append("rect")
          .attr("class", function(d,i) {return 'legend cluster' + i;})
          .attr("x", width - 10)
          .attr("width", 10)
          .attr("height", 10)
          .attr("fill", function(d,i){return colorScheme[i]});

        legend.append("text")
          .data(data)
          .attr("x", width - 20)
          .attr("y", 6)
          .attr("dy", ".35em")
          .style("text-anchor", "end")
          .text(function (d) { return d.description;})

        function legendMouseover(d,i){
            var sel = d3.selectAll('.node-container .cluster' + i )
                .classed("bubble-hover", true)
                .classed("stroke", true)
        } 
        function legendMouseout(d){
            var sel = d3.selectAll('.bubble-hover' )
                .classed("bubble-hover", false)
        } 


        //GROUPS
        var nodeContainer = svg.append("g")
                            .attr("class","node-container")
        var node = nodeContainer.selectAll("circle")
            .data(nodes)
            .enter().append("g")
            .attr("class", function(d){return "cluster"+d.cluster;})
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
            .attr("dx", textDx)
            .attr("dy", ".35em")
            .attr("font-size", fontSize)
            .text(function (d) {return d.name})
            .style("stroke", "none")
            .style("fill", textFill)


        function textDx(d){
            return (-(5 * d.radius/minRadius) * d.name.length)/2
        }

        function fontSize(d){
            //function of the radius
            return ''+ (10 * d.radius/minRadius) + 'px'; 
                
        }

        function textFill(d){
            var background = color(d.cluster);
            return brightness(d3.rgb(background)) < 120 ? "#fff" : "#000";
        };





        function tick(e) {
            var jitter = 0.2;
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
