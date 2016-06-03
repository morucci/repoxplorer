function gen_histo(histo) {
  var svg_histo = dimple.newSvg("#history", 1240, 250);
  var chart_histo = new dimple.chart(svg_histo, histo);
  chart_histo.addCategoryAxis("x", "date");
  chart_histo.addMeasureAxis("y", "value");
  chart_histo.setBounds(30, 30, 1200, 150);
  chart_histo.addSeries(null, dimple.plot.bar);
  chart_histo.draw();
}

function gen_top_author_pie(pie_top) {
  var svg_pie_top = dimple.newSvg("#topauthors_pie", 700, 400);
  var chart_pie_top = new dimple.chart(svg_pie_top, pie_top);
  chart_pie_top.setBounds(20, 20, 400, 340)
  chart_pie_top.addMeasureAxis("p", "amount");
  chart_pie_top.addSeries("email", dimple.plot.pie);
  chart_pie_top.addLegend(500, 20, 200, 390, "right");
  chart_pie_top.draw();
}

function gen_top_author_modified_pie(pie_top_m) {
  var svg_pie_top_m = dimple.newSvg("#topauthors_m_pie", 700, 400);
  var chart_pie_top_m = new dimple.chart(svg_pie_top_m, pie_top_m);
  chart_pie_top_m.setBounds(20, 20, 400, 340)
  chart_pie_top_m.addMeasureAxis("p", "amount");
  chart_pie_top_m.addSeries("email", dimple.plot.pie);
  chart_pie_top_m.addLegend(500, 20, 200, 300, "right");
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

function get_commits(pid, page) {
 if (page === undefined) {
       page = 0;
 }
 $.getJSON(
   "/commits.json", {pid : pid,
                     start : page,
                     dfrom: getUrlParameter('dfrom'),
                     dto: getUrlParameter('dto')}
 ).done(function(data) {
   $("#commits-table").empty()
   $("#commits-table").append("<table class=\"table table-striped\">");
   var theader = "<tr>"
   theader += "<th>Date of commit</th>"
   theader += "<th>Project</th>"
   theader += "<th>Author</th>"
   theader += "<th>Committer</th>"
   theader += "<th>Message</th>"
   theader += "<th>Modified lines</th>"
   theader += "</tr>"
   $("#commits-table table").append(theader);
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
    // Just use the first gitweb link atm
    if (v['gitwebs'][0].length > 0) {
     elm += "<td><a href=" + v['gitwebs'][0] + ">" + v['commit_msg'] + "</a></td>"
    } else {
     elm += "<td>" + v['commit_msg'] + "</td>"
    }
    elm += "<td>" + v['line_modifieds'] + "</td>"
    elm += "</tr>"
    $("#commits-table table").append(elm);
   })
   $("#commits-table").append("</table>");
  })
  .fail(function(err) {console.log(err)})
}

function check_fragment() {
    var hash = window.location.hash || "#page-1";
    hash = hash.match(/^#page-(\d+)$/);
    if(hash)
        page = parseInt(hash[1])
        $("#pagination").pagination('selectPage', page);
};

function install_paginator(pid, items_amount) {
 $(window).bind("popstate", check_fragment);
 $(function() {
     $('#pagination').pagination({
         items: items_amount,
         itemsOnPage: 10,
         cssStyle: 'light-theme',
         onPageClick: function(pageNumber) {
             get_commits(pid, (pageNumber - 1) * 10)
         }
     });
     check_fragment();
 });
}
