const url_string = new URL(`${window.origin}/dendapi`)
const hg_id = window.location.pathname.split('/')[3]
url_string.searchParams.append('hg', hg_id)

const width = document.getElementById("svg").clientWidth - 100
var height = 750
var margin = {top: 50, right: 50, bottom: 50, left: 50}


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

    console.log(nodes, links)

    canvas.append("g")
        .attr("class", "rects")
        .selectAll("rect")
        .data(nodes)
        .join("rect")
        .attr("x", d => d.x0 + 1)
        .attr("y", d => d.y0)
        .attr("height", d => d.y1 - d.y0)
        .attr("width", d => d.x1 - d.x0 - 2)
        // .attr("fill", d => d.color = color(d.id.replace(/ .*/, "")))
        .attr("fill", d => d.color)
        .append("title")
        .text(d => `${d.id}`)

    const link = canvas.append("g")
        .attr("fill", "none")
        .selectAll(".rect")
        .data(links)
        .join("g")
        .attr("class", "link")
        .attr("stroke", d => d.source.color)
        .attr("stroke-opacity", 0.2)

    link.append("path")
        .attr("d", d3.sankeyLinkHorizontal())
        .attr("stroke-width", d => Math.max(1, d.width))

    link.append("title")
        .text(d => `${d.source.id} --> ${d.target.id}`)

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
        .attr("y", d => (d.y1 + d.y0) / 2 - 15)
        .attr("x", d => d.x0 < width / 2 ? d.x1 + 6 : d.x0 - 6)
        .text(d => `  ${d.art}`)

    console.log(link)
}

console.log("DONE");