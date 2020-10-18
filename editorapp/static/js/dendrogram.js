const url_string = new URL(`${window.origin}/dendapi`)

const width = document.getElementById("svg").clientWidth - 20
var height = 600
var margin = {top: 10, right: 10, bottom: 10, left: 10}


var canvas = d3.select("#svg").append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

// console.log(canvas)

var color = d3.scaleOrdinal(d3.schemeCategory10);

// console.log(snek)

d3.json(url_string).then(data => {  // https://www.d3-graph-gallery.com/sankey.html
    // console.log(error)
    renderSnek(data);
});

function renderSnek(data) {
    // console.log(graph);
    // console.log(graph.nodes);
    // console.log(graph.links);
    //
    // var snek = d3.sankey()
    //     .nodeWidth(36)
    //     .nodePadding(290)
    //     .size([width, height]);
    //     // .iterations(1);
    // // snek.nodes(graph.nodes);
    // // snek.links(graph.links);
    // // console.log(snek.nodes(graph.nodes))
    // //
    // // snek
    // //     .nodes(graph.nodes)
    // //     .links(graph.links);
    // //     // .layout(1)
    //
    // const {nodes, links} = snek({nodes: graph.nodes, links: graph.links})
    //
    // console.log(snek);
    // console.log(snek.links);
    // console.log(snek.nodes);
    //
    // var link = canvas.append("g")
    //     .attr("fill", "none")
    //     .attr("stroke", "#000")
    //     .attr("stroke-opacity", 0.2)
    //     .selectAll("path")
    //     .data(graph.links)
    //     .join("path")
    //     .attr("d", d3.sankeyLinkHorizontal())
    //     .attr("stroke-width", d => d.width);
    //
    // // var link = canvas.append("g")
    // //     .selectAll(".link")
    // //     .data(graph.links)
    // //     .enter()
    // //     .append("path")
    // //     .attr("class", "link")
    // //     .attr("d", d3.sankeyLinkHorizontal())
    // //     .style("stroke-width", d => Math.max(1, d.dy))
    // //     .sort((a, b) => b.dy - a.dy)
    //
    // var node = canvas.append("g")
    //     .selectAll(".node")
    //     .data(graph.nodes)
    //     .enter().append("g")
    //     .attr("class", "node")
    //     .attr("transform", d => `translate(${d.x},${d.y})`)
    //     .call(d3.drag()
    //         .subject( d => d )
    //         .on("start", function() {
    //             this.parentNode.appendChild(this)
    //         })
    //         .on("drag", dragmove));
    //
    // node
    //     .append("rect")
    //     .attr("height", d => d.dy)
    //     .attr("width", snek.nodeWidth())
    //     .style("fill", d => d.color = color(d.id.replace(/ .*/, "")))
    //     .style("stroke", d => d3.rgb(d.color).darker(2))
    //     .append("title")
    //     .text(d => d.name + "\n" + "This is a label");
    //
    // node
    //     .append("text")
    //     .attr("x", -6)
    //     .attr("y", d => d.dy/2)
    //     .attr("dy", ".35em")
    //     .attr("text-anchor", "end")
    //     .attr("transform", null)
    //     .text(d => d.id)
    //     .filter(d => d.x < width/2)
    //     .attr("x", 6 + snek.nodeWidth())
    //     .attr("text-anchor", "start");
    //
    // function dragmove(d){
    //     d3.select(this)
    //         .attr("transform", `translate(${d.x},${(d.y = Math.max(0, Math.min(height - d.dy, d3.event.y)))})`)
    //     snek.relayout()
    //     link.attr("d", snek.link())
    // }
    sankey = d3.sankey()
        // .nodeAlign(d3[`sankey${align[0].toUpperCase()}${align.slice(1)}`])
        // .nodeSort(inputOrder ? null : undefined)
        .nodeWidth(15)
        .nodePadding(10)
        .extent([[0, 5], [width, height - 5]])

    const {nodes, links} = sankey({
        nodes: data.nodes,
        links: data.links
    })

    canvas.append("g")
        .attr("class", "rects")
        .selectAll("rect")
        .data(nodes)
        .join("rect")
        .attr("x", d => d.x0 + 1)
        .attr("y", d => d.y0)
        .attr("height", d => d.y1 - d.y0)
        .attr("width", d => d.x1 - d.x0 - 2)
        .attr("fill", d => d.color = color(d.id.replace(/ .*/, "")))
        .append("title")
        .text(d => `${d.id} label`)

    const link = canvas.append("g")
        .attr("fill", "none")
        .selectAll(".rects")
        .data(links)
        .join("g")
        .attr("stroke", "#000")
        .attr("stroke-opacity", 0.2)

    link.append("path")
        .attr("d", d3.sankeyLinkHorizontal())
        .attr("stroke-width", d => Math.max(1, d.width))

    link.append("title")
        .text(d => `${d.source.id} -> ${d.target.id} \n this is the link title`)

    canvas.append("g")
        .style("font", "10px sans-serif")
        .selectAll("text")
        .data(nodes)
        .join("text")
        .attr("x", d => d.x0 < width / 2 ? d.x1 + 6 : d.x0 - 6)
        .attr("y", d => (d.y1 + d.y0) / 2)
        .attr("dy", "0.35em")
        .attr("text-anchor", d => d.x0 < width / 2 ? "start" : "end")
        .text(d => d.id)
        .append("tspan")
        .attr("fill-opacity", 0.7)
        .text(d => `WTF is dis`)

    console.log(link)
}

console.log("DONE");