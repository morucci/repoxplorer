function gen_histo(histo) {
  var svg_histo = dimple.newSvg("#history", 800, 350);
  var chart_histo = new dimple.chart(svg_histo, histo);
  chart_histo.addCategoryAxis("x", "date");
  chart_histo.addMeasureAxis("y", "value");
  chart_histo.setBounds(30, 30, 750, 250);
  chart_histo.addSeries(null, dimple.plot.bar);
  chart_histo.draw();
}

function gen_top_author_pie(pie_top) {
  var svg_pie_top = dimple.newSvg("#topauthors_pie", 590, 400);
  var chart_pie_top = new dimple.chart(svg_pie_top, pie_top);
  chart_pie_top.setBounds(20, 20, 400, 340)
  chart_pie_top.addMeasureAxis("p", "amount");
  chart_pie_top.addSeries("name", dimple.plot.pie);
  chart_pie_top.addLegend(500, 20, 90, 300, "right");
  chart_pie_top.draw();
}

function gen_top_author_modified_pie(pie_top_m) {
  var svg_pie_top_m = dimple.newSvg("#topauthors_m_pie", 590, 400);
  var chart_pie_top_m = new dimple.chart(svg_pie_top_m, pie_top_m);
  chart_pie_top_m.setBounds(20, 20, 400, 340)
  chart_pie_top_m.addMeasureAxis("p", "amount");
  chart_pie_top_m.addSeries("name", dimple.plot.pie);
  chart_pie_top_m.addLegend(500, 20, 90, 300, "right");
  chart_pie_top_m.draw();
}

function getUrlParameter(sParam) {
    var sPageURL = decodeURIComponent(window.location.search.substring(1)),
        sURLVariables = sPageURL.split('&'),
        sParameterName,
        i;

    for (i = 0; i < sURLVariables.length; i++) {
        sParameterName = sURLVariables[i].split('=');

        if (sParameterName[0] === sParam) {
            return sParameterName[1] === undefined ? true : sParameterName[1];
        }
    }
};

function install_date_pickers(projectid) {
 $(function() {
   var dfrom = getUrlParameter('dfrom')
   var dto = getUrlParameter('dto')
   $( "#fromdatepicker" ).datepicker();
   $( "#fromdatepicker" ).datepicker('setDate', dfrom);
   $( "#todatepicker" ).datepicker();
   $( "#todatepicker" ).datepicker('setDate', dto);
 });

 $("#filter").click(function(){
  var newlocation = "project.html?pid=" + projectid
  if ($('#fromdatepicker').val() != '') {
    newlocation = newlocation + "&dfrom=" + encodeURIComponent($('#fromdatepicker').val())
  }
  if ($('#todatepicker').val() != '') {
    newlocation = newlocation + "&dto=" + encodeURIComponent($('#todatepicker').val())
  }
  window.location = newlocation
  });
}

function get_commits(pid) {
 $.getJSON(
   "/commits.json", {pid : pid,
                     dfrom: getUrlParameter('dfrom'),
                     dto: getUrlParameter('dto')}
 ).done(function(data) {
   $("#commits").append("<table border='1'>");
   var theader = "<tr>"
   theader += "<th>Date of commit</th>"
   theader += "<th>Project</th>"
   theader += "<th>Author</th>"
   theader += "<th>Committer</th>"
   theader += "<th>Message</th>"
   theader += "</tr>"
   $("#commits table").append(theader);
   $.each( data[2], function(k, v) {
    var cmt_date = new Date(1000 * v['committer_date']);
    var elm = "<tr>"
    var projects = ""
    $.each(v['projects'], function(i, p) {
      if (i > 0) {projects += "<br>"}
      projects += p
    })
    elm += "<td>" + cmt_date.toUTCString() + "</td>"
    elm += "<td>" + projects + "</td>"
    elm += "<td>" + v['author_name'] + "</td>"
    elm += "<td>" + v['committer_name'] + "</td>"
    elm += "<td>" + v['commit_msg'] + "</td>"
    elm += "</tr>"
    $("#commits table").append(elm);
   })
   $("#commits").append("</table>");
  })
  .fail(function(err) {console.log(err)})
}
