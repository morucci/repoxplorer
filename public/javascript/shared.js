function gen_histo(histo) {
  var svg_histo = dimple.newSvg("#history", '100%', 250);
  var chart_histo = new dimple.chart(svg_histo, histo);
  chart_histo.addCategoryAxis("x", "date");
  chart_histo.addMeasureAxis("y", "value");
  chart_histo.setMargins("60px", "30px", "60px", "70px");
  chart_histo.addSeries(null, dimple.plot.bar);
  chart_histo.draw();
  $( window ).resize(function() {
    chart_histo.draw(0, true);
  })
};

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

 if (getUrlParameter('inc_merge_commit') == 'on') {
    $('#inc_merge_commit').prop('checked', true)
 }

 if (getUrlParameter('inc_projects')) {
     selected = getUrlParameter('inc_projects').split(',')
     $('#subprojects').val(selected)
 }

 $("#filter").click(function(){
  var newlocation = "project.html?pid=" + projectid
  if ($('#fromdatepicker').val() != '') {
    newlocation = newlocation + "&dfrom=" + encodeURIComponent($('#fromdatepicker').val())
  }
  if ($('#todatepicker').val() != '') {
    newlocation = newlocation + "&dto=" + encodeURIComponent($('#todatepicker').val())
  }
  if ($('#inc_merge_commit').prop('checked')) {
      newlocation = newlocation + "&inc_merge_commit=on"
  }
  if ($('#subprojects').val() != undefined) {
    newlocation = newlocation + "&inc_projects=" + encodeURIComponent($('#subprojects').val())
  }
  window.location = newlocation
  });
}

function get_commits(pid, page) {
 if (page === undefined) {
   page = 0;
 }
 if ($('#inc_merge_commit').prop('checked')) {
   var inc_merge_commit = 'on'
 }
 $.getJSON(
   "/commits.json", {pid : pid,
                     start : page,
                     dfrom: getUrlParameter('dfrom'),
                     dto: getUrlParameter('dto'),
                     inc_merge_commit: inc_merge_commit,
                     inc_projects: getUrlParameter('inc_projects')}
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
   theader += "<th>Time To Land</th>"
   theader += "</tr>"
   $("#commits-table table").append(theader);
   $.each( data[2], function(k, v) {
    var cmt_date = new Date(1000 * v['committer_date']);
    var cmt_date = moment(cmt_date)
    var elm = "<tr>"
    var projects = ""
    $.each(v['projects'], function(i, p) {
      if (i > 0) {projects += "<br>"}
      projects += p
    })
    elm += "<td>" + cmt_date.format("MMM D, YYYY") + "</td>"
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
    elm += "<td>" + v['ttl'] + "</td>"
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
 if (items_amount >= 1000) {
   // Limit the amount of pages to 100
   // User should use the calendar filter to dig in the results
   items_amount = 1000
 }
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
