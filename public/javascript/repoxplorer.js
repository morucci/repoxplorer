function is_cookies_enabled() {
    var isEnabled = (navigator.cookieEnabled) ? true : false;
    if ( typeof navigator.cookieEnabled == "undefined" && !cookieEnabled ) {
        document.cookie='test';
        isEnabled = (document.cookie.indexOf('test')!=1) ? true : false;
    }
    return isEnabled;
}

function get_value_of_key(target, key) {
    var tokens = target.split(/%3B/); // semi-colon
    for ( var i = 0; i < tokens.length; i++ ) {
        var keyvalue = tokens[i].split(/%3D/);
        if ( key.indexOf(keyvalue[0]) == 0 ) {
            return keyvalue[1];
        }
    }
    return false;
}

var entityMap = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;',
  '/': '&#x2F;',
  '`': '&#x60;',
  '=': '&#x3D;'
};

function escapeHtml(string) {
  return String(string).replace(/[&<>"'`=\/]/g, function (s) {
    return entityMap[s];
  });
}

function get_username() {
    var username = '';
    if ( is_cookies_enabled() ) {
        var tokens = document.cookie.split(';');
        for ( var i = 0; i < tokens.length; i++ ) {
            tokens[i] = tokens[i].trim();
            if ( tokens[i].indexOf('auth_pubtkt') == 0 ) {
                var username = get_value_of_key(tokens[i].substring(12), 'uid');
            }
        }
    };
    return escapeHtml(username);
};

function get_user_infos(login) {
  return $.getJSON("api/v1/users/" + login);
}

function delete_user(login) {
    return $.ajax({
        url: "api/v1/users/" + login,
        type: 'DELETE',
    });
}

function init_menu() {
  $.getJSON("api/v1/status/status")
    .done(function(status) {
        // Fill menu with status info
        $("#version").append(
            '<a href="#">Version:' + status.version + '</a>');
        $("#intro-paragraph").append(
            "<h2>" + status.projects + " projects over " + status.repos + " Git repositories are indexed on this repoXplorer instance. You'll find stats about them and their contributors.</h2>");
        $("#intro-paragraph").append(status.customtext);
        // If user backend activated check if user is logged then init menu
        if (status['users_endpoint']) {
          if (get_username() != '') {
            // Logged in
            $("#ls-switch").empty()
            $("#contrib-page").empty()
            get_user_infos(get_username())
              .done(
                function(udata) {
                  $("#ls-switch").append('<a href="home.html">My account</a>')
                  $("#contrib-page").append('<a href="contributor.html?cid='+ udata['cid'] +'">My contributions</a>')
                })
              .error(
                function(err) {
                  console.log("Unabled to fetch user account: " + err)
                  // Assume not logged, cookie no longer valid ?
                  $("#ls-switch").empty()
                  $("#contrib-page").empty()
                  $("#ls-switch").append('<a href="home.html"><b>Claim your contributions/Login</b></a>')
                })
          } else {
            // Not logged
            $("#ls-switch").empty()
            $("#contrib-page").empty()
            $("#ls-switch").append('<a href="home.html"><b>Claim your contributions/Login</b></a>')
          }
        }
    })
    .fail(function(err) {
        console.log("Unabled to get server status: " + err);
    });
}

function gen_histo(histo, id) {
    var svg_histo = dimple.newSvg("#"+id, '100%', 250);
    var chart_histo = new dimple.chart(svg_histo, histo);
    chart_histo.addCategoryAxis("x", "date");
    chart_histo.addMeasureAxis("y", "value");
    chart_histo.setMargins("60px", "30px", "60px", "70px");
    chart_histo.addSeries(null, dimple.plot.bar);
    chart_histo.draw();
    $( window ).resize(function() {
        chart_histo.draw(0, true);
    });
}

function getUrlParameter(sParam) {
    var sPageURL = window.location.search.substring(1),
        sURLVariables = sPageURL.split('&'),
        sParameterName,
        i;

    for (i = 0; i < sURLVariables.length; i++) {
        sParameterName = sURLVariables[i].split('=');

        if (sParameterName[0] === sParam) {
            return sParameterName[1] === undefined ? true : decodeURIComponent(sParameterName[1]);
        }
    }
}

function install_date_pickers() {
    var dfrom = getUrlParameter('dfrom');
    var dto = getUrlParameter('dto');
    $("#fromdatepicker").datepicker(
        {dateFormat: "yy-mm-dd",
         changeMonth: true,
         changeYear: true});
    $("#fromdatepicker").datepicker('setDate', dfrom);
    $("#todatepicker").datepicker(
        {dateFormat: "yy-mm-dd",
         changeMonth: true,
         changeYear: true});
    $("#todatepicker").datepicker('setDate', dto);
}

function get_groups(nameonly, withstats, prefix) {
    var args = {};
    args['nameonly'] = nameonly;
    args['withstats'] = withstats;
    args['prefix'] = prefix;
    return $.getJSON("api/v1/groups/", args);
}

function get_histo(pid, tid, cid, gid, type) {
    // TODO: move checkbox value retrieval outside
    if ($('#inc_merge_commit').prop('checked')) {
        var inc_merge_commit = 'on';
    }
    var args = {};
    args['pid'] = pid;
    args['tid'] = tid;
    args['cid'] = cid;
    args['gid'] = gid;
    args['dfrom'] = getUrlParameter('dfrom');
    args['dto'] = getUrlParameter('dto');
    args['inc_merge_commit'] = inc_merge_commit;
    args['inc_repos'] = getUrlParameter('inc_repos');
    args['metadata'] = getUrlParameter('metadata');
    args['exc_groups'] = getUrlParameter('exc_groups');
    args['inc_groups'] = getUrlParameter('inc_groups');
    return $.getJSON("api/v1/histo/" + type, args);
}

function get_top(pid, tid, cid, gid, type, stype, limit) {
    // TODO: move checkbox value retrieval outside
    if ($('#inc_merge_commit').prop('checked')) {
        var inc_merge_commit = 'on';
    }
    if ($('#inc_repos_detail').prop('checked')) {
        var inc_repos_detail = 'true';
    }
    var args = {
        'pid': pid,
        'tid': tid,
        'cid': cid,
        'gid': gid,
        'dto': getUrlParameter('dto'),
        'dfrom': getUrlParameter('dfrom'),
        'inc_merge_commit': inc_merge_commit,
        'inc_repos_detail': inc_repos_detail,
        'inc_repos': getUrlParameter('inc_repos'),
        'metadata': getUrlParameter('metadata'),
        'exc_groups': getUrlParameter('exc_groups'),
        'inc_groups': getUrlParameter('inc_groups'),
        'limit': limit
    };
    return $.getJSON("api/v1/tops/" + type + "/" + stype, args);
}

function get_top_diff(pid, tid, cid, gid, infos, dtoref_dfrom, limit) {
    // TODO: move checkbox value retrieval outside
    if ($('#inc_merge_commit').prop('checked')) {
        var inc_merge_commit = 'on';
    }
    if ($('#inc_repos_detail').prop('checked')) {
        var inc_repos_detail = 'true';
    }
    var args = {
        'pid': pid,
        'tid': tid,
        'cid': cid,
        'gid': gid,
        'dfromref': dtoref_dfrom.format("YYYY-MM-DD"),
        'dtoref': moment(infos.first * 1000).format("YYYY-MM-DD"),
        'dfrom': moment(infos.first * 1000).format("YYYY-MM-DD"),
        'dto': moment(infos.last * 1000).format("YYYY-MM-DD"),
        'inc_merge_commit': inc_merge_commit,
        'inc_repos_detail': inc_repos_detail,
        'inc_repos': getUrlParameter('inc_repos'),
        'metadata': getUrlParameter('metadata'),
        'exc_groups': getUrlParameter('exc_groups'),
        'inc_groups': getUrlParameter('inc_groups'),
        'limit': limit
    };
    return $.getJSON("api/v1/tops/authors/diff", args);
}

function fill_info_box(args) {
    $("#infos-commits_amount").empty();
    $("#infos-authors_amount").empty();
    $("#infos-duration").empty();
    $("#infos-first_commit").empty();
    $("#infos-last_commit").empty();
    $("#infos-lines_changed").empty();
    $("#infos-author_name").empty();
    $("#infos-gravatar").empty();
    $("#infos-projects_amount").empty();
    $("#infos-repos_amount").empty();
    $("#infos-repos_amount-alt").empty();
    $("#infos-known_emails").empty();
    $("#infos-description").empty();
    $("#infos-members_amount").empty();


    $("#infos-commits_amount").append('<b>Commits:</b> ' + args.commits_amount);
    $("#infos-authors_amount").append('<b>Authors:</b> ' + args.authors_amount);
    $("#infos-duration").append('<b>Activity duration:</b> ' + args.duration + ' days');
    $("#infos-first_commit").append('<b>Date of first commit:</b> '+ moment(args.first).format("YYYY-MM-DD HH:mm:ss"));
    $("#infos-last_commit").append('<b>Date of last commit:</b> ' + moment(args.last).format("YYYY-MM-DD HH:mm:ss"));
    $("#infos-lines_changed").append('<b>Lines changed:</b> ' + args.line_modifieds_amount);
    $("#infos-author_name").append('<b>Full Name:</b> ' + args.name);
    $("#infos-gravatar").append('<img class="img-responsive" src="https://www.gravatar.com/avatar/' + args.gravatar + '?s=150" title="' + args.name + '">');
    $("#infos-projects_amount").append('<b>Projects contributed:</b> ' + args.projects_amount);
    $("#infos-repos_amount").append('<b>Repository refs contributed:</b> ' + args.repos_amount);
    $("#infos-repos_amount-alt").append('<b>Repository refs:</b> ' + args.repos_amount);
    $("#infos-known_emails").append('<b>Known emails:</b> ' + args.mails_amount);
    if (args.description) {
        $("#infos-description").append('<b>Description:</b> ' + args.description);
    }
    $("#infos-members_amount").append('<b>Members:</b> ' + args.members_amount);
    if (args.bots_group) {
        $("#infos-bots-group").empty();
        $("#infos-bots-group").append('<b>Bots group:</b> ' + "<a href='group.html?gid=" + args.bots_group + "'>" + args.bots_group + '</a>');
    }
}

function get_infos(pid, tid, cid, gid) {
    // TODO: move checkbox value retrieval outside
    if ($('#inc_merge_commit').prop('checked')) {
        var inc_merge_commit = 'on';
    }
    var args = {};
    args['pid'] = pid;
    args['tid'] = tid;
    args['cid'] = cid;
    args['gid'] = gid;
    args['dfrom'] = getUrlParameter('dfrom');
    args['dto'] = getUrlParameter('dto');
    args['inc_merge_commit'] = inc_merge_commit;
    args['inc_repos'] = getUrlParameter('inc_repos');
    args['metadata'] = getUrlParameter('metadata');
    args['exc_groups'] = getUrlParameter('exc_groups');
    args['inc_groups'] = getUrlParameter('inc_groups');

    gr_d = $.when();
    gc_d = $.when();
    gg_d = $.when();
    gp_d = $.when();

    if(pid || tid) {
        gr_d = $.getJSON("api/v1/projects/repos",
                         {'pid': pid, 'tid': tid});
    }
    if (pid) {
        gp_d = $.getJSON("api/v1/projects/projects", {'pid': pid});
    }
    if(cid) {
        gc_d = $.getJSON("api/v1/infos/contributor", {'cid': cid});
    }
    if (gid) {
        gg_d = $.getJSON("api/v1/groups/", {'prefix': gid});
    }

    gi_d = $.getJSON("api/v1/infos/infos", args);
    return $.when(gr_d, gi_d, gc_d, gg_d, gp_d)
        .done(
            function(rdata, idata, cdata, gdata, pdata) {
                if (cid) {
                    cdata = cdata[0];
                }
                if (gid) {
                    gdata = gdata[0][gid];
                }
                if (pid) {
                    pdata = pdata[0][pid];
                }
                idata = idata[0];
                var ib_data = {};

                ib_data.duration = parseInt(moment.duration(1000 * idata.duration).asDays());
                ib_data.first = new Date(1000 * idata.first);
                ib_data.last = new Date(1000 * idata.last);
                ib_data.commits_amount = idata.commits_amount;
                ib_data.authors_amount = idata.authors_amount;
                ib_data.line_modifieds_amount = idata.line_modifieds_amount;
                ib_data.projects_amount = idata.projects_amount;
                ib_data.repos_amount = idata.repos_amount;
                if (cid) {
                    ib_data.name = escapeHtml(cdata.name);
                    ib_data.gravatar = cdata.gravatar;
                    ib_data.mails_amount = cdata.mails_amount;
                }
                if (gid) {
                    ib_data.description = escapeHtml(gdata.description);
                    ib_data.members_amount = Object.keys(gdata.members).length;
                }
                if (pid) {
                  ib_data.description = pdata.description;
                  ib_data.bots_group = pdata['bots-group'];
                }
                fill_info_box(ib_data);
                $("#infos-progress").empty();
            })
        .fail(
            function(err) {
                console.log(err);
                $("#infos-progress").empty();
                if (err.status == 404) {
                    msg = '<string>' + err.responseJSON.message + '</strong>';
                    set_error_msg(msg);
                }
            });
}

function set_error_msg(msg) {
    $("#error-msg").append(msg);
    $("#error-box").show();
    $("#infos_filters_div").hide();
    $("#commits_histo_div").hide();
    $("#contributors_histo_div").hide();
    $("#top_authors_c_div").hide();
    $("#top_authors_lc_div").hide();
    $("#top_projects_c_div").hide();
    $("#top_projects_lc_div").hide();
    $("#commits_listing_div").hide();
    $("#top_authors_new").hide();
}

function create_alpha_index(groups) {
    r = {};
    sr = [];
    for (group in groups) {
        i = group[0].toLowerCase();
        if (r[i]) {
            r[i]++;
        } else {
            r[i] = 1;
        }
    }
    for (k in r) {
        sr.push(k);
    }
    sr.sort();
    return [r, sr];
}

function build_top_authors_head(top, label) {
    top_h = '<div class="row-fluid">';
    for (i = 0; i < top.length; i++) {
        if ( i > 2 ) { break; };
        var pos;
        if (i == 0) { pos = "1 st"; }
        if (i == 1) { pos = "2 nd"; }
        if (i == 2) { pos = "3 rd"; }
        top_h += '<div class="col-md-4">';
        top_h += '<div align="center"><p><b><h3>' + pos + '</h3></b></p></div>';
        top_h += '<div align="center"><p><b><h4>' + top[i].amount + ' ' + label + ' </h4></b></p></div>';
        top_h += '<div align="center"><a href=contributor.html?cid=' + top[i].cid + '>' +
            '<img class="img-responsive" src="https://www.gravatar.com/avatar/' +
            top[i].gravatar + '?s=150" title=' + escapeHtml(top[i].name) + '></a></div>';
        top_h += '<div align="center"><p><b><h3><a href=contributor.html?cid=' +
            top[i].cid + '>' + escapeHtml(top[i].name) + '</a></h3></b></p></div>';
        top_h += '</div>';
    };
    return top_h;
}

function build_top_authors_body(top, btid_more, limit) {
    top_b = '<table class="table table-striped">';
    top_b += '<tr><th class="col-md-1">Rank</th><th>Name</th><th>Amount</th></tr>';
    for (i = 3; i < top.length; i++) {
        top_b += '<tr>';
        rank = i + 1;
        top_b += '<td>' + rank + '</td>';
        top_b += '<td></span><span style="padding-right: 5px">' +
            '<img src="https://www.gravatar.com/avatar/' +
            top[i].gravatar + '?s=25" title="' + escapeHtml(top[i].name) + '">' +
            '</span><span><b><a href=contributor.html?cid=' +
            top[i].cid + '>' + escapeHtml(top[i].name) + '</a></b></span></td>';
        top_b += '<td>' + top[i].amount + '</td>';
        top_b += '</tr>';
    }
    top_b += '</table>';
    top_b += '<div class="col-md-5"></div>';
    top_b += '<div class="col-md-1">';
    top_b += '<button type="button" id="' + btid_more + '" class="btn btn-link">display more</button>';
    top_b += '</div>';
    top_b += '<div class="col-md-5"></div>';
    return top_b;
}
function build_top_projects_table(top, inc_repos_detail, btid_more, limit) {
    top_b = '<table class="table table-striped">';
    if (inc_repos_detail == true) {
    top_b += '<tr><th class="col-md-1">Rank</th><th>Project</th><th>Name</th><th>Amount</th></tr>';
    } else {
        top_b += '<tr><th class="col-md-1">Rank</th><th>Name</th><th>Amount</th></tr>';
    }
    for (i = 0; i < top.length; i++) {
        top_b += '<tr>';
        rank = i + 1;
        top_b += '<td>' + rank + '</td>';
        if (inc_repos_detail == true) {
            // A ref can be found in multiple project ... simply use the first item
            top_b += '<td><a href="project.html?pid=' + top[i].projects[0] + '">' + top[i].projects[0] + '</a></td>';
            top_b += '<td><a href="project.html?pid=' + top[i].projects[0] + '&inc_repos=' + top[i].name + '">' + top[i].name +'</a></span> ';
        }
        else {
            top_b += '<td><a href="project.html?pid=' + top[i].name + '">' + top[i].name + '</a></td>';
        }
        top_b += '<td>' + top[i].amount + '</td>';
        top_b += '</tr>';
    }
    top_b += '</table>';
    top_b += '<div class="col-md-5"></div>';
    top_b += '<div class="col-md-1">';
    top_b += '<button type="button" id="' + btid_more + '" class="btn btn-link">display more</button>';
    top_b += '</div>';
    top_b += '<div class="col-md-5"></div>';
    return top_b;
}

function index_page_init() {
    init_menu();
}

function user_page_init() {
  init_menu();

  $("#user-settings-form").submit(function(event) {
    // Make sure the browser does not honor the default submit behavior
    event.preventDefault();

    // Create the data structure from the form
    var data = {
      'uid': $("#username").val(),
      'name': $("#fullname").val(),
      'default-email': $("#demail").val(),
      'emails': [],
    }
    $.each($("input[id='email']"), function(i, semail) {
      email_obj = {
        'email': semail.value,
        'groups': [],
      }
      $.each($("select[id*='group ']"), function(i, sgroup) {
        if (sgroup.id.split(' ')[1] != semail.value) { return; }
        if (sgroup.value != '') {
          group_obj = {'group': sgroup.value}
          dfrom = sgroup.parentNode.parentNode.parentNode.childNodes[1].childNodes[1].childNodes[0].value
          if (dfrom != '') {
            group_obj['begin-date'] = moment(dfrom, "YYYY-MM-DD").valueOf() / 1000
          }
          dto = sgroup.parentNode.parentNode.parentNode.childNodes[2].childNodes[1].childNodes[0].value
          if (dto != '') {
            group_obj['end-date'] = moment(dto, "YYYY-MM-DD").valueOf() / 1000
          }
          email_obj.groups.push(group_obj)
        }
      });
      data.emails.push(email_obj);
    });

    // Send the data server side
    // console.log('Sending ' + JSON.stringify(data))
    $("#settings-progress").show();
    $.ajax({
      url: "api/v1/users/" + $("#username").val(),
      type: "POST",
      data: JSON.stringify(data),
      contentType:"application/json; charset=utf-8",
      dataType:"json",
      success: function(){
        $("#submit-msg").empty()
        $("#submit-msg").addClass("alert-success");
        $("#submit-msg").append("Your settings have been submitted successfuly");
        $("#submit-box").show();
        $("#settings-progress").hide();
      },
      error: function() {
        $("#submit-msg").empty()
        $("#submit-msg").addClass("alert-warning");
        $("#submit-msg").append("Sorry, server side error");
        $("#submit-box").show();
        $("#settings-progress").hide();
      }
    })
  });

  // After we have fetched groups info and user info
  gg_d = get_groups('true')
  // Username is fetched from the cauth cookie
  gui_d = get_user_infos(get_username())
  return $.when(gg_d, gui_d)
    .done(
      function(gdata, udata) {
        gdata = gdata[0]
        udata = udata[0]

        // Fill the jumbotron
        $("#jumbotron_block").empty();
        $("#jumbotron_block").append(
            '<h2>Welcome ' + escapeHtml(udata["name"]) + '. On this page you can modify your settings.'
        );

        $("#username").val(udata["uid"]);
        $("#fullname").val(escapeHtml(udata["name"]));
        $("#demail").val(udata["default-email"]);

        // For each email prepare the form
        $.each(udata["emails"], function(i, obj) {
          email_html_form = '<div class="form-group">' +
          '<label for="email" class="col-md-4 control-label">Email ' + (i + 1) + '</label>' +
          '<span class="col-md-2">' +
          '<input class="form-control" id="email" type="text" value="' + obj.email + '" disabled>' +
          '</span>' +
          '<span class="col-md-2">' +
          '<button type="button" class="btn btn-default" id="email-'+i+'" data-email="'+obj.email+'">Add group membership</button>' +
          '</span>' +
          '</div>'

          // For each group add a selector to the form
          email_html_form += '<div id="groups-list-'+i+'">'
          $.each(obj.groups, function(j, group) {
            email_html_form += '<div><div class="form-group">'
            email_html_form += '<label for="group ' + obj.email + ' ' + j + '" class="col-md-5 control-label">Member of group</label>' +
            '<div class="col-md-2">' +
            '<select class="form-control" id="group ' + obj.email + ' ' + j +'">'
            $.each(gdata, function(gname) {
              selected = ''
              if (gname == group.group) {
                selected = "selected"
              };
              email_html_form += '<option value="' + gname + '"' + selected + '>' + gname + '</option>'
            });
            email_html_form += '</select></div>'
            email_html_form += '<button id="remove-'+j+'" type="button" class="btn btn-default btn-md">'
            email_html_form += '<span class="glyphicon glyphicon-remove" aria-hidden="true"></span>'
            email_html_form += '</button>'
            email_html_form += '</div>'
            email_html_form += '<div class="form-group">'
            email_html_form += '<label class="col-md-5 control-label" for="fromdatepicker-' + i + '-' + j + '">From date</label>'
            email_html_form += '<span class="col-md-3"><input type="text" class="form-control" id="fromdatepicker-' + i + '-' + j + '"></span>'
            email_html_form += '</div>'
            email_html_form += '<div class="form-group">'
            email_html_form += '<label class="col-md-5 control-label" for="todatepicker-' + i + '-' + j + '">To date</label>'
            email_html_form += '<span class="col-md-3"><input type="text" class="form-control" id="todatepicker-' + i + '-' + j + '"></span>'
            email_html_form += '</div>'
          });
          email_html_form += '</div>'

          $("#emails").append(email_html_form)

          // do the remove selector bind afterward, to make it works
          $.each(obj.groups, function(j, group) {
            $("#remove-"+j).on("click", function(){
              $(this).parent().parent().remove();
            });
            $("#fromdatepicker-" + i + '-' + j).datepicker(
                {dateFormat: "yy-mm-dd",
                 changeMonth: true,
                 changeYear: true});
            if ('begin-date' in group) {
              $("#fromdatepicker-" + i + '-' + j).datepicker(
                'setDate', moment(group['begin-date'] * 1000).format("YYYY-MM-DD"));
            }
            $("#todatepicker-" + i + '-' + j).datepicker(
                {dateFormat: "yy-mm-dd",
                 changeMonth: true,
                 changeYear: true});
            if ('end-date' in group) {
              $("#todatepicker-" + i + '-' + j).datepicker(
                'setDate', moment(group['end-date'] * 1000).format("YYYY-MM-DD"));
            }
          });

          // Add the binding to add new group selector
          $("#email-"+i).on("click", function(e){
            eindex = e.currentTarget.id.split('-')[1]
            email = e.currentTarget.getAttribute("data-email")
            group_selector = '<div><div class="form-group">'
            mid = Math.floor(Math.random() * (1000 - 100) + 100);
            group_selector += '<label for="group ' + email + ' ' + mid + '" class="col-md-5 control-label">Member of group</label>' +
            '<div class="col-md-2">' +
            '<select class="form-control" id="group ' + email + ' ' + mid +'">'
            group_selector += '<option disabled selected value> -- select a group -- </option>'
            $.each(gdata, function(gname) {
              group_selector += '<option value="' + gname + '">' + gname + '</option>'
            });
            group_selector += '</select></div>'
            group_selector += '<button id="remove-'+mid+'" type="button" class="btn btn-default btn-md">'
            group_selector += '<span class="glyphicon glyphicon-remove" aria-hidden="true"></span>'
            group_selector += '</button>'
            group_selector += '</div>'
            group_selector += '<div class="form-group">'
            group_selector += '<label class="col-md-5 control-label" for="fromdatepicker-' + mid + '">From date</label>'
            group_selector += '<span class="col-md-3"><input type="text" class="form-control" id="fromdatepicker-' + mid + '"></span>'
            group_selector += '</div>'
            group_selector += '<div class="form-group">'
            group_selector += '<label class="col-md-5 control-label" for="todatepicker-' + mid + '">To date</label>'
            group_selector += '<span class="col-md-3"><input type="text" class="form-control" id="todatepicker-' + mid + '"></span>'
            group_selector += '</div>'

            group_selector += '</div>'
            $("#groups-list-"+eindex).append(group_selector)
            $("#remove-"+mid).on("click", function(){
              $(this).parent().parent().remove();
            });
            $("#fromdatepicker-" + mid).datepicker(
                {dateFormat: "yy-mm-dd",
                 changeMonth: true,
                 changeYear: true});
            $("#todatepicker-" + mid).datepicker(
                {dateFormat: "yy-mm-dd",
                 changeMonth: true,
                 changeYear: true});
          });
        });
        $("#settings-progress").hide();
      }
    )
  .fail(
      function(err) {
        $("#submit-msg").empty()
        $("#submit-msg").addClass("alert-warning");
        $("#submit-msg").append("Sorry, server side error");
        $("#submit-box").show();
        $("#settings-progress").hide();
      }
    );
}

function projects_page_init() {
    init_menu();

    function fill_result(data) {
        $("#project-results").empty();
        $("#tag-results").empty();

        var tagoutput = '<div class="col-md-12">';

        if (data['tags'].length > 0) {
            tagoutput += '<div class="panel panel-default">' +
                   '<div class="panel-heading">' +
                   '<h3 class="panel-title text-left"><b>Tags</b></h3>' +
                   '</div>' +
                   '<div class="panel-body">' +
                   '<h4>';
            $.each(data['tags'], function(key, tag) {
                tagoutput +='<a href="project.html?tid=' + tag + '">' + tag + '</a> ';
            });
            tagoutput += '</h4></div></div>';
        }
        tagoutput += '</div>';
        $("#tag-results").append(tagoutput);


        var i;
        projectarray = [];
        $.each(data['projects'], function(k, value) {
            var project_hash = {key: k, value: data['projects'][k]};
            projectarray.push(project_hash);
        });
        var chunk_size =  Math.ceil(projectarray.length / 3);

        for (i=0; i<3; i++)
        {
            temparray = projectarray.slice(i * chunk_size, i * chunk_size + chunk_size);
            var box = '<div class="col-md-4" >';
            $.each(temparray, function(k, v) {
                box += '<div class="panel panel-default panel-project" id="project-panel-' +
                          v.key + '">' +
                          '<div class="panel-body">' +
                          '<div class="row-fluid row-flex" id="project-panel-row">' +
                          '<div class="col-md-2 project-panel-logo">';

                if (v.value.logo) {
                    box += '<img src="data:image/png;base64,' + v.value.logo + '">';
                } else {
                    box += '<img src="https://www.gravatar.com/avatar/?s=50">';
                }

                box +=    '</div> '+
                          '<div class="col-md-9 project-panel-name">' +
                          '<h2><a href="project.html?pid=' + v.key + '"><b>' + v.key + '</b></a></h2></div>' +
                          '<div class="col-md-1">' +
                          '<a id="toggle-button-' + v.key + '" class="btn btn-default">' +
                          '<i class="glyphicon glyphicon-menu-down project-panel-button" aria-hidden="true"></i></a></div>';

                var middle = '<div class="col-md-12 project-panel-detail" id="project-panel-detail">' +
                             '<div class="blank-separator"></div>';

                if (v.value.description) {
                    middle += '<h3>' + v.value.description + '</h3>';
                    middle += '<div class="blank-separator"></div>';
                }
                middle += '<table class="table">';
                middle += '<tr>';
                middle += '<th>Repository</th>';
                middle += '<th>Branches</th>';
                middle += '</tr>';

                var repos = {};
                $.each(v.value['refs'], function(key, repo) {
                    if (!(repo.name in repos)) {
                        repos[repo.name] = [];
                        repos[repo.name].push(repo.branch);
                    } else {
                        repos[repo.name].push(repo.branch);
                    }
                });
                repo_keys = Object.keys(repos);
                repo_keys.sort();

                var line ='<tr>';
                $.each(repo_keys, function(rid, rname) {
                    line += '<td><a href="project.html?pid=' + v.key;
                    line += '&inc_repos=';
                    branches = repos[rname];
                    $.each(branches, function(i, bname) {
                        var sep = ',';
                        if (i === 0) {
                            sep = '';
                        }
                        line += sep + rname + ':' + bname;
                    });
                    line += '">' + rname + '</a></td>';
                    line += '<td>';
                    $.each(branches, function(i, bname) {
                        line += '<span><a href="project.html?pid=' + v.key + '&inc_repos=' + rname + ':' + bname + '">' + bname +'</a></span> ';
                    });
                    line += '</td>';
                    line += '</tr>';
                });

                middle += line;
                middle += '</table></div></div></div></div>';

                box += middle;
            });
            box += '</div>';
            $("#project-results").append(box);
        }
    }

    $("#page-title").append("[RepoXplorer] - Projects listing");

    $.getJSON("api/v1/projects/projects")
        .done(
            function(data) {
                fill_result(data);
            })
        .fail(
            function(err) {
                console.log(err);
            });

    $(document).on('click',"a[id^=toggle-button-]",function(){
        $(this).find('i').toggleClass('glyphicon-menu-down').toggleClass('glyphicon-menu-up');
        $(this).parent().parent().find('#project-panel-detail').toggle();
    });
}

function groups_page_init() {
    init_menu();

    $("#page-title").append("[RepoXplorer] - Groups listing");
    $("#groups-table-progress").append(
        '&nbsp;<span class="glyphicon glyphicon-refresh glyphicon-refresh-animate"></span>');
    var prefix = getUrlParameter('prefix');
    var ggn_d = get_groups('true');
    ggn_d
        .done(function(data) {
            ret = create_alpha_index(data);
            index = ret[0];
            sindex = ret[1];
            $("#groups-index").empty();
            $.each(sindex, function(i, v) {
                p = v.toUpperCase();
                $("#groups-index").append(
                    "<span id='groups-index'><a href='groups.html?prefix=" + v + "'><b>" + p + " </b></a></span>");
            });
        })
        .fail(function(err) {
            console.log(err);
        });
    $.when(ggn_d)
        .done(function() {
            if (prefix === undefined) {
                prefix = sindex[0];
            }
            var gg_d = get_groups('false', 'false', prefix);
            gg_d
                .done(
                    function(data) {
                        $("#groups-table-progress").empty();
                        $("#groups-table").empty();
                        $("#groups-table").append("<table class=\"table table-striped\">");
                        var theader = "<tr>";
                        theader += "<th>Group name</th>";
                        theader += "<th>Group domains</th>";
                        theader += "<th>Group description</th>";
                        theader += "<th>Group members</th>";
                        $("#groups-table table").append(theader);
                        groups = [];
                        $.each(data, function(gid, gdata) {
                            groups.push(gid);
                        });
                        groups.sort();
                        $.each(groups, function(i, gid) {
                            var elm = "<tr>";
                            elm += "<td><a href=group.html?gid=" + encodeURIComponent(gid) + ">" + gid + "</a></td>";
                            elm += "<td>" + data[gid]['domains'] + "</td>";
                            elm += "<td>" + data[gid]['description'] + "</td>";
                            elm += "<td>";
                            $.each(data[gid]['members'], function(cid, cdata) {
                                elm += "<span style='padding-right: 5px'><img src='https://www.gravatar.com/avatar/" +
                                    cdata['gravatar'] + "?s=20'></span><span style='padding-right: 5px'>" +
                                    "<a href=contributor.html?cid=" + cid + ">" + escapeHtml(cdata['name']) + "</a></span>";
                            });
                            elm += "</td>";
                            $("#groups-table table").append(elm);
                        });
                        $("#groups-table").append("</table>");
                    })
                .fail(
                    function(err) {
                        $("#groups-table-progress").empty();
                        console.log(err);
                    });
            });
}

function contributor_page_init() {
    init_menu();

    install_date_pickers();

    cid = getUrlParameter('cid');
    pid = getUrlParameter('pid');

    if (!cid) {
        set_error_msg("The mandatory cid parameter is missing. Please provide it.");
        return;
    }

    if (getUrlParameter('inc_merge_commit') == 'on') {
        $('#inc_merge_commit').prop('checked', true);
    }
    var inc_repos_detail = false;
    if (getUrlParameter('inc_repos_detail') == 'on') {
        inc_repos_detail = true;
        $('#inc_repos_detail').prop('checked', true);
    }

    $("#filter").click(function(){
        var newlocation = "contributor.html?cid=" + cid;
        if ($('#fromdatepicker').val() != '') {
            newlocation = newlocation + "&dfrom=" + encodeURIComponent($('#fromdatepicker').val());
        }
        if ($('#todatepicker').val() != '') {
            newlocation = newlocation + "&dto=" + encodeURIComponent($('#todatepicker').val());
        }
        if ($('#inc_merge_commit').prop('checked')) {
            newlocation = newlocation + "&inc_merge_commit=on";
        }
        if ($('#inc_repos_detail').prop('checked')) {
            newlocation = newlocation + "&inc_repos_detail=on";
        }
        if ($('#projects-filter').val() != undefined) {
            newlocation = newlocation + "&pid=" + encodeURIComponent($('#projects-filter').val());
        }
        window.location = newlocation;
    });

    $.getJSON("api/v1/projects/projects")
        .done(
            function(data) {
                $('#projects-filter')
                    .find('option')
                    .remove()
                    .end();
                $('#projects-filter').append($('<option>', {
                    text: 'Select a project',
                    value: ''
                }));
                names = [];
                $.each(data['projects'], function(i, o) {
                    names.push(i);
                });
                names.sort();
                $.each(names, function(i, v) {
                    $('#projects-filter').append($('<option>', {
                        text: v,
                        value: v
                    }));
                });
                if (getUrlParameter('pid')) {
                    $('#projects-filter').val(getUrlParameter('pid'));
                }
            })
        .fail(
            function(err) {
                console.log(err);
            });

    $("#releasesmodal").on('show.bs.modal', function (event) {
        var button = $(event.relatedTarget);
        pickupdatetarget = button.data('datetarget');

        $.getJSON("api/v1/projects/projects")
            .done(
                function(data) {
                    $('#projects')
                        .find('option')
                        .remove()
                        .end();
                    $('#releases')
                        .find('option')
                        .remove()
                        .end();
                    $('#projects').append($('<option>', {
                        text: 'Select a project',
                        value: ''
                    }));
                    $.each(data['projects'], function(i, o) {
                        $('#projects').append($('<option>', {
                            text: i,
                            value: i
                        }));
                    });
                })
            .fail(
                function(err) {
                    console.log(err);
                });
    }),
    $("#selectrelease").click(function(){
        var rdate = $('#releases').val();
        if (pickupdatetarget === 'fromdatepicker') {$( "#fromdatepicker" ).datepicker('setDate', rdate);}
        if (pickupdatetarget === 'todatepicker')  {$( "#todatepicker" ).datepicker('setDate', rdate);}
    });

    $('#projects').on('change', function() {
        $('#releases')
            .find('option')
            .remove()
            .end();
        if (this.value === '') {return 1;}
        get_releases(this.value);
    });

    d = get_infos(pid, undefined, cid, undefined);
    d.done(function(rdata, idata, cdata, gdata) {
        idata = idata[0];
        cdata = cdata[0];
        if(idata.commits_amount > 0) {
            install_paginator(pid, undefined, cid, undefined, idata.commits_amount, true);
            get_commits(pid, undefined, cid, undefined, undefined, true);

            // Fill the title
            $("#page-title").append("[" + escapeHtml(cdata.name) + "] - Contributor stats");

            // Fill the jumbotron
            $("#jumbotron_block").empty();
            $("#jumbotron_block").append(
                "<h2><a href=contributor.html?cid=" + cid + ">" + escapeHtml(cdata.name) + "</a>'s contributor stats</h2>"
            );

            // Fill the histo commits selector
            $("#history-progress").append(
                '&nbsp;<span class="glyphicon glyphicon-refresh glyphicon-refresh-animate"></span>');
            var c_h_deferred = get_histo(pid, undefined, cid, undefined, 'commits');
            c_h_deferred
                .done(function(data) {
                    $("#history-progress").empty();
                    gen_histo(data, 'history');
                })
                .fail(function(err) {
                    $("#history-progress").empty();
                    console.log(err);
                });

            // Fill the top project by commits
            function fill_top_projects_by_commits(limit) {
              $("#topprojects-bycommits-progress").append(
                  '&nbsp;<span class="glyphicon glyphicon-refresh glyphicon-refresh-animate"></span>');
              var top_projects_commit_deferred = get_top(
                  pid, undefined, cid, undefined, 'projects', 'bycommits', limit);
              top_projects_commit_deferred
                  .done(function(top) {
                      $("#topprojects-bycommits-progress").empty();
                      $("#topprojects").empty();
                      top_t = build_top_projects_table(
                          top, inc_repos_detail, 'tabpc-dmore');
                      $("#topprojects").append(top_t);
                      $('#tabpc-dmore').click(function() {
                          limit = limit + 10;
                          fill_top_projects_by_commits(limit);
                      });
                  })
                  .fail(function(err) {
                      $("#topprojects-bycommits-progress").empty();
                      $("#topprojects").empty();
                      console.log(err);
                  });
              }
            fill_top_projects_by_commits(10);

            // Fill the top project by lines changed
            function fill_top_projects_by_lchanged(limit) {
              $("#topprojects-bylchanged-progress").append(
                  '&nbsp;<span class="glyphicon glyphicon-refresh glyphicon-refresh-animate"></span>');
              var top_projects_lchanged_deferred = get_top(
                  pid, undefined, cid, undefined, 'projects', 'bylchanged', limit);
              top_projects_lchanged_deferred
                  .done(function(top) {
                      $("#topprojects-bylchanged-progress").empty();
                      $("#topprojects_m").empty();
                      top_t = build_top_projects_table(
                          top, inc_repos_detail, 'tabplc-dmore');
                      $("#topprojects_m").append(top_t);
                      $('#tabplc-dmore').click(function() {
                          limit = limit + 10;
                          fill_top_projects_by_lchanged(limit);
                        });
                  })
                  .fail(function(err) {
                      $("#topprojects-bylchanged-progress").empty();
                      $("#topprojects_m").empty();
                      console.log(err);
                  });
              }
            fill_top_projects_by_lchanged(10);
        } else {
            $("#empty-warning").show();
            $("#infos-duration").hide();
            $("#infos-first_commit").hide();
            $("#infos-last_commit").hide();
            $("#infos-projects_amount").hide();
            $("#infos-repos_amount").hide();
            $("#commits_histo_div").hide();
            $("#top_projects_c_div").hide();
            $("#top_projects_lc_div").hide();
            $("#commits_listing_div").hide();
        }
    });
}

function group_page_init(commits_amount) {
    init_menu();

    install_date_pickers();

    gid = getUrlParameter('gid');
    pid = getUrlParameter('pid');

    if (!gid) {
        set_error_msg("The mandatory gid parameter is missing. Please provide it.");
        return;
    }

    $("#page-title").append("[" + gid + "] - Group stats");

    if (getUrlParameter('inc_merge_commit') == 'on') {
        $('#inc_merge_commit').prop('checked', true);
    }

    var inc_repos_detail = false;
    if (getUrlParameter('inc_repos_detail') == 'on') {
        inc_repos_detail = true;
        $('#inc_repos_detail').prop('checked', true);
    }

    $.getJSON("api/v1/projects/projects")
        .done(
            function(data) {
                $('#projects-filter')
                    .find('option')
                    .remove()
                    .end();
                $('#projects-filter').append($('<option>', {
                    text: 'Select a project',
                    value: ''
                }));
                names = [];
                $.each(data['projects'], function(i, o) {
                    names.push(i);
                });
                names.sort();
                $.each(names, function(i, v) {
                    $('#projects-filter').append($('<option>', {
                        text: v,
                        value: v
                    }));
                });
                if (getUrlParameter('pid')) {
                    $('#projects-filter').val(getUrlParameter('pid'));
                }
            })
        .fail(
            function(err) {
                console.log(err);
            });

    $("#releasesmodal").on('show.bs.modal', function (event) {
        var button = $(event.relatedTarget);
        pickupdatetarget = button.data('datetarget');

        $.getJSON("api/v1/projects/projects")
            .done(
                function(data) {
                    $('#projects')
                        .find('option')
                        .remove()
                        .end();
                    $('#releases')
                        .find('option')
                        .remove()
                        .end();
                    $('#projects').append($('<option>', {
                        text: 'Select a project',
                        value: ''
                    }));
                    $.each(data['projects'], function(i, o) {
                        $('#projects').append($('<option>', {
                            text: i,
                            value: i
                        }));
                    });
                })
            .fail(
                function(err) {
                    console.log(err);
                });
    });

    $("#selectrelease").click(function(){
        var rdate = $('#releases').val();
        if (pickupdatetarget === 'fromdatepicker') {$( "#fromdatepicker" ).datepicker('setDate', rdate);}
        if (pickupdatetarget === 'todatepicker')  {$( "#todatepicker" ).datepicker('setDate', rdate);}
    });

    $("#filter").click(function(){
        var newlocation = "group.html?gid=" + gid;
        if ($('#fromdatepicker').val() != '') {
            newlocation = newlocation + "&dfrom=" + encodeURIComponent($('#fromdatepicker').val());
        }
        if ($('#todatepicker').val() != '') {
            newlocation = newlocation + "&dto=" + encodeURIComponent($('#todatepicker').val());
        }
        if ($('#inc_merge_commit').prop('checked')) {
            newlocation = newlocation + "&inc_merge_commit=on";
        }
        if ($('#inc_repos_detail').prop('checked')) {
            newlocation = newlocation + "&inc_repos_detail=on";
        }
        if ($('#projects-filter').val() != undefined) {
            newlocation = newlocation + "&pid=" + encodeURIComponent($('#projects-filter').val());
        }
        window.location = newlocation;
    });

    $('#projects').on('change', function() {
        $('#releases')
            .find('option')
            .remove()
            .end();
        if (this.value === '') {return 1;}
        get_releases(this.value);
    });

    d = get_infos(pid, undefined, undefined, gid);
    d.done(function(rdata, idata, cdata, gdata) {
        idata = idata[0];

        if(idata.commits_amount > 0) {
            install_paginator(pid, undefined, undefined, gid, idata.commits_amount, true);
            get_commits(pid, undefined, undefined, gid, undefined, true);

            // Fill the jumbotron
            $("#jumbotron_block").empty();
            link = '<h2><a href="group.html?gid=' + gid + '">' + gid + '</a>\'s group stats</h2>'
            $("#jumbotron_block").append(link);

            // Fill the histo commits selector
            $("#history-progress").append(
                '&nbsp;<span class="glyphicon glyphicon-refresh glyphicon-refresh-animate"></span>');
            var c_h_deferred = get_histo(pid, undefined, undefined, gid, 'commits');
            c_h_deferred
                .done(function(data) {
                    $("#history-progress").empty();
                    gen_histo(data, 'history');
                })
                .fail(function(err) {
                    $("#history-progress").empty();
                    console.log(err);
                });

            // Fill the histo author selector
            $("#history-author-progress").append(
                '&nbsp;<span class="glyphicon glyphicon-refresh glyphicon-refresh-animate"></span>');
            var cont_h_deferred = get_histo(pid, undefined, undefined, gid, 'authors');
            cont_h_deferred
                .done(function(data) {
                    $("#history-author-progress").empty();
                    gen_histo(data, 'history_author');
                })
                .fail(function(err) {
                    $("#history-author-progress").empty();
                    console.log(err);
                });

            // Fill the top project by commits
            function fill_top_projects_by_commits(limit) {
              $("#topprojects-bycommits-progress").append(
                  '&nbsp;<span class="glyphicon glyphicon-refresh glyphicon-refresh-animate"></span>');
              var top_projects_commit_deferred = get_top(
                  pid, undefined, undefined, gid, 'projects', 'bycommits', limit);
              top_projects_commit_deferred
                  .done(function(top) {
                      $("#topprojects-bycommits-progress").empty();
                      $("#topprojects").empty();
                      top_t = build_top_projects_table(
                          top, inc_repos_detail, 'tabpc-dmore');
                      $("#topprojects").append(top_t);
                      $('#tabpc-dmore').click(function() {
                          limit = limit + 10;
                          fill_top_projects_by_commits(limit);
                      });
                  })
                  .fail(function(err) {
                      $("#topprojects-bycommits-progress").empty();
                      $("#topprojects").empty();
                      console.log(err);
                  });
              }
            fill_top_projects_by_commits(10);

            // Fill the top project by lines changed
            function fill_top_projects_by_lchanged(limit) {
              $("#topprojects-bylchanged-progress").append(
                  '&nbsp;<span class="glyphicon glyphicon-refresh glyphicon-refresh-animate"></span>');
              var top_projects_lchanged_deferred = get_top(
                  pid, undefined, undefined, gid, 'projects', 'bylchanged', limit);
              top_projects_lchanged_deferred
                  .done(function(top) {
                      $("#topprojects-bylchanged-progress").empty();
                      $("#topprojects_m").empty();
                      top_t = build_top_projects_table(
                          top, inc_repos_detail, 'tabplc-dmore');
                      $("#topprojects_m").append(top_t);
                      $('#tabplc-dmore').click(function() {
                          limit = limit + 10;
                          fill_top_projects_by_lchanged(limit);
                        });
                  })
                  .fail(function(err) {
                      $("#topprojects-bylchanged-progress").empty();
                      $("#topprojects_m").empty();
                      console.log(err);
                  });
              }
            fill_top_projects_by_lchanged(10);

            // Fill the top authors by commits
            function fill_top_authors_by_commits(limit) {
                $("#topauthor-bycommits-progress").append(
                    '&nbsp;<span class="glyphicon glyphicon-refresh glyphicon-refresh-animate"></span>');
                var top_auth_commit_deferred = get_top(
                    pid, undefined, undefined, gid, 'authors', 'bycommits', limit);
                top_auth_commit_deferred
                    .done(function(top) {
                        $("#topauthor-bycommits-progress").empty();
                        $("#topauthors_gravatar").empty();
                        $("#topauthors").empty();
                        top_h = build_top_authors_head(top, 'commits');
                        $("#topauthors_gravatar").append(top_h);
                        if (top.length > 3) {
                            top_b = build_top_authors_body(top, 'tabc-dmore', limit);
                            $("#topauthors").append(top_b);
                            $('#tabc-dmore').click(function() {
                                limit = limit + 10;
                                fill_top_authors_by_commits(limit);
                            });
                        }
                    })
                    .fail(function(err) {
                        $("#topauthor-bycommits-progress").empty();
                        $("#topauthors_gravatar").empty();
                        $("#topauthors").empty();
                        console.log(err);
                    });
            }
            fill_top_authors_by_commits(10);

            // Fill the top authors by line changed
            function fill_top_authors_by_lchanged(limit) {
                $("#topauthor-bylchanged-progress").append(
                    '&nbsp;<span class="glyphicon glyphicon-refresh glyphicon-refresh-animate"></span>');
                var top_auth_lchanged_deferred = get_top(
                    pid, undefined, undefined, gid, 'authors', 'bylchanged', limit);
                top_auth_lchanged_deferred
                    .done(function(top) {
                        $("#topauthor-bylchanged-progress").empty();
                        $("#topauthors_m_gravatar").empty();
                        $("#topauthors_m").empty();
                        top_h = build_top_authors_head(top, 'lines changed');
                        $("#topauthors_m_gravatar").append(top_h);
                        if (top.length > 3) {
                            top_b = build_top_authors_body(top, 'tablc-dmore', limit);
                            $("#topauthors_m").append(top_b);
                            $('#tablc-dmore').click(function() {
                                limit = limit + 10;
                                fill_top_authors_by_lchanged(limit);
                            });
                        }
                    })
                    .fail(function(err) {
                        $("#topauthor-bylchanged-progress").empty();
                        $("#topauthors_m_gravatar").empty();
                        $("#topauthors_m").empty();
                        console.log(err);
                    });
            }
            fill_top_authors_by_lchanged(10);

        } else {
            $("#empty-warning").show();
            $("#commits_histo_div").hide();
            $("#contributors_histo_div").hide();
            $("#top_projects_c_div").hide();
            $("#top_projects_lc_div").hide();
            $("#top_authors_c_div").hide();
            $("#top_authors_lc_div").hide();
            $("#commits_listing_div").hide();
        }
    });
}

function project_page_init() {
    init_menu();

    install_date_pickers();

    var selected_metadata = [];
    $("#newsincerelease").datepicker(
        {dateFormat: "yy-mm-dd",
         changeMonth: true,
         changeYear: true});
    var newsinceval;

    pid = getUrlParameter('pid');
    tid = getUrlParameter('tid');

    if (!pid && !tid) {
        set_error_msg("Mandatory parameters pid or tid are missing. Please provide one.");
        return;
    }
    if (pid && tid) {
        set_error_msg("pid and tid are exclusives parameters.");
        return;
    }

    if (pid) {
        $("#page-title").append("[" + pid + "] - Project stats");
        $("#jumbotron_block").append(
            '<h2><a href="project.html?pid=' + pid + '">' + pid + '</a>\'s project stats</h2>'
        );
    } else {
        $("#page-title").append("[" + tid + "] - Project tag stats");
        $("#jumbotron_block").append(
            '<h2><a href="projects.html?cid=' + tid + '">' + tid + '</a>\'s tag stats</h2>'
        );
    }

    if (getUrlParameter('inc_merge_commit') == 'on') {
        $('#inc_merge_commit').prop('checked', true);
    }

    if (getUrlParameter('inc_') == 'on') {
        $('#inc_merge_commit').prop('checked', true);
    }
    if (getUrlParameter('inc_merge_commit') == 'on') {
        $('#inc_merge_commit').prop('checked', true);
    }
    if (getUrlParameter('inc_groups')) {
        $('#inc_groups').prop('checked', true);
    }
    if (getUrlParameter('exc_groups')) {
        $('#exc_groups').prop('checked', true);
    }

    if (getUrlParameter('metadata')) {
        selected_metadata = getUrlParameter('metadata').split(',');
        $.each(selected_metadata, function(i, v) {
            $("#metadata-selected").append('<span class="badge">'+v+'</div>');
        });
    }

    var newlocation;

    $("#filter").click(function(){
        if (pid) {
            newlocation = "project.html?pid=" + pid;
        }
        else {
            newlocation = "project.html?tid=" + tid;
        }
        if ($('#fromdatepicker').val() != '') {
            newlocation = newlocation + "&dfrom=" + encodeURIComponent($('#fromdatepicker').val());
        }
        if ($('#todatepicker').val() != '') {
            newlocation = newlocation + "&dto=" + encodeURIComponent($('#todatepicker').val());
        }
        if ($('#inc_merge_commit').prop('checked')) {
            newlocation = newlocation + "&inc_merge_commit=on";
        }
        if ($('#repositories').val() != undefined) {
            newlocation = newlocation + "&inc_repos=" + encodeURIComponent($('#repositories').val());
        }
        if ($('#groups').val() != "") {
          if ($('#inc_groups').prop("checked")) {
            newlocation = newlocation + "&inc_groups=" + encodeURIComponent($('#groups').val());
          }
          if ($('#exc_groups').prop("checked")) {
            newlocation = newlocation + "&exc_groups=" + encodeURIComponent($('#groups').val());
          }
        }
        if (selected_metadata.length > 0) {
            newlocation = newlocation + "&metadata=" + encodeURIComponent(selected_metadata.toString());
        }
        window.location = newlocation;
    });

    $("#add-to-filter").click(function(){
        metadata = $('#metadata').val();
        value = $('#metadata-values').val();
        if (metadata === '') {return 1;}
        selected_metadata.push(metadata + ":" + value);
        $("#metadata-selected").html("");
        $.each(selected_metadata, function(i, v) {
            $("#metadata-selected").append('<span class="badge">'+v+'</div>');
        });
    });

    $("#clean-filter").click(function(){
        selected_metadata = [];
        $("#metadata-selected").html("");
    });

    var pickupdatetarget = undefined;
    $('#releasesmodal').on('show.bs.modal', function (event) {
        var button = $(event.relatedTarget);
        pickupdatetarget = button.data('datetarget');
    });

    function fill_top_new_authors(infos, dtoref_dfrom, limit) {
        $("#topnewauthors-progress").append(
            '&nbsp;<span class="glyphicon glyphicon-refresh glyphicon-refresh-animate"></span>');
        if ($('#fromdatepicker').val() != '') {
          var top_new_authors_deferred = get_top_diff(
              pid, tid, undefined, undefined, infos, dtoref_dfrom, limit);
        } else {
          var top_new_authors_deferred = $.Deferred();
          top_new_authors_deferred.resolve();
        }
        top_new_authors_deferred
            .done(function(top) {
                $("#topnewauthors_gravatar").empty();
                $("#topnewauthors").empty();
                $("#topnewauthors-progress").empty();
                if ($('#fromdatepicker').val() != '') {
                    top_h = build_top_authors_head(top, 'commits');
                    $("#topnewauthors_gravatar").append(top_h);
                    if (top.length > 3) {
                        top_b = build_top_authors_body(top, 'tna-dmore', limit);
                        $("#topnewauthors").append(top_b);
                        dtoref_dfrom_orig = dtoref_dfrom;
                        dtoref_dfrom = dtoref_dfrom.format("YYYY-MM-DD");
                        dfromref = moment(infos.first * 1000).format("YYYY-MM-DD");
                        dto = moment(infos.last * 1000).format("YYYY-MM-DD");
                        $('#difftxt').text(
                            "During the period from " + dfromref + " to " + dto + " compared to the period from " + dtoref_dfrom + " to " + dfromref);
                        $('#tna-dmore').click(function() {
                            limit = limit + 10;
                            fill_top_new_authors(infos, dtoref_dfrom_orig, limit);
                        });
                    }
                } else {
                   $('#difftxt').text("No from date selected. Please select an initial date in the Filters box to see new authors.");
                }
            })
            .fail(function(err) {
                $("#topnewauthors-progress").empty();
                $("#topnewauthors_gravatar").empty();
                $("#topnewauthors").empty();
                $('#diffduring').empty();
                $('#diffref').empty();
                console.log(err);
            });
    }

    // Fill the groups selector
    var defer = get_groups('true');
    defer.done(
        function(data) {
            $('#groups')
                .find('option')
                .remove()
                .end();
            $('#groups').append($('<option>', {
                text: 'Select a group',
                value: ''
            }));
            groups = [];
            $.each(data, function(k, v) {
                groups.push(k);
            });
            groups.sort();
            $.each(groups, function(i, k) {
                $('#groups').append($('<option>', {
                    text: k,
                    value: k
                }));
            });
            if (getUrlParameter('exc_groups')) {
                groups = getUrlParameter('exc_groups').split(',');
                $('#groups').val(groups);
            }
            if (getUrlParameter('inc_groups')) {
                groups = getUrlParameter('inc_groups').split(',');
                $('#groups').val(groups);
            }
        }
    )
        .fail(
            function(err) {
                console.log(err);
            }
        );

    // Get the info and continue to fill the page if commits_amount is > 0
    d = get_infos(pid, tid, undefined, undefined);
    d.done(function(rdata, idata, cdata, gdata) {
        idata = idata[0];
        rdata = rdata[0];
        if (idata.commits_amount > 0) {
            $("#selectrelease").click(function(){
                var rdate = $('#releases').val();
                if (pickupdatetarget === 'fromdatepicker') {
                    $("#fromdatepicker").datepicker('setDate', rdate);
                }
                if (pickupdatetarget === 'todatepicker') {
                    $("#todatepicker").datepicker('setDate', rdate);
                }
                if (pickupdatetarget === 'newsincerelease') {
                    $("#newsincerelease").val(rdate);
                    newsinceval = $('#newsincerelease').val();
                    dtoref_dfrom = moment(newsinceval, "YYYY-MM-DD");
                    fill_top_new_authors(idata, dtoref_dfrom, 10);
                }
            });
            install_paginator(
                pid, tid, undefined,
                undefined, idata.commits_amount, true);

            get_metadata_keys(pid, tid, undefined);

            get_commits(
                pid, tid, undefined, undefined,
                undefined, true);

            get_releases(pid, tid);

            // Fill project refs selector
            refs = [];
            $.each(rdata, function(i, v) {
                val = v.name + ':' + v.branch;
                refs.push(val);
            });
            refs.sort();
            $.each(refs, function(i, ref) {
                $('#repositories').append($('<option>', {
                    text: ref,
                    value: ref
                }));
            });
            // Select the ones specified in the url
            if (getUrlParameter('inc_repos')) {
                selected = getUrlParameter('inc_repos').split(',');
                $('#repositories').val(selected);
            }

            // Fill the histo commits selector
            $("#history-progress").append(
                '&nbsp;<span class="glyphicon glyphicon-refresh glyphicon-refresh-animate"></span>');
            var c_h_deferred = get_histo(pid, tid, undefined, undefined, 'commits');
            c_h_deferred
                .done(function(data) {
                    $("#history-progress").empty();
                    gen_histo(data, 'history');
                })
                .fail(function(err) {
                    $("#history-progress").empty();
                    console.log(err);
                });

            // Fill the histo author selector
            $("#history-author-progress").append(
                '&nbsp;<span class="glyphicon glyphicon-refresh glyphicon-refresh-animate"></span>');
            var cont_h_deferred = get_histo(pid, tid, undefined, undefined, 'authors');
            cont_h_deferred
                .done(function(data) {
                    $("#history-author-progress").empty();
                    gen_histo(data, 'history_author');
                })
                .fail(function(err) {
                    $("#history-author-progress").empty();
                    console.log(err);
                });
            // Fill the top new authors
            if (newsinceval === undefined) {
                newsinceval = $('#newsince').val();
                dtoref_dfrom = moment(idata.first * 1000).subtract(newsinceval, 'seconds');
                fill_top_new_authors(idata, dtoref_dfrom, 10);
            }
            $('#newsince').change(function() {
                newsinceval = $('#newsince').val();
                dtoref_dfrom = moment(idata.first * 1000).subtract(newsinceval, 'seconds');
                fill_top_new_authors(idata, dtoref_dfrom, 10);
            });
            $('#newsincerelease').change(function() {
                newsinceval = $('#newsincerelease').val();
                dtoref_dfrom = moment(newsinceval, "YYYY-MM-DD");
                fill_top_new_authors(idata, dtoref_dfrom, 10);
            });

            // Fill the top authors by commits
            function fill_top_authors_by_commits(limit) {
                $("#topauthor-bycommits-progress").append(
                    '&nbsp;<span class="glyphicon glyphicon-refresh glyphicon-refresh-animate"></span>');
                var top_auth_commit_deferred = get_top(
                    pid, tid, undefined, undefined, 'authors', 'bycommits', limit);
                top_auth_commit_deferred
                    .done(function(top) {
                        $("#topauthor-bycommits-progress").empty();
                        $("#topauthors_gravatar").empty();
                        $("#topauthors").empty();
                        top_h = build_top_authors_head(top, 'commits');
                        $("#topauthors_gravatar").append(top_h);
                        if (top.length > 3) {
                            top_b = build_top_authors_body(top, 'tabc-dmore', limit);
                            $("#topauthors").append(top_b);
                            $('#tabc-dmore').click(function() {
                                limit = limit + 10;
                                fill_top_authors_by_commits(limit);
                            });
                        }
                    })
                    .fail(function(err) {
                        $("#topauthor-bycommits-progress").empty();
                        $("#topauthors_gravatar").empty();
                        $("#topauthors").empty();
                        console.log(err);
                    });
            }
            fill_top_authors_by_commits(10);

            // Fill the top authors by line changed
            function fill_top_authors_by_lchanged(limit) {
                $("#topauthor-bylchanged-progress").append(
                    '&nbsp;<span class="glyphicon glyphicon-refresh glyphicon-refresh-animate"></span>');
                var top_auth_lchanged_deferred = get_top(
                    pid, tid, undefined, undefined, 'authors', 'bylchanged', limit);
                top_auth_lchanged_deferred
                    .done(function(top) {
                        $("#topauthor-bylchanged-progress").empty();
                        $("#topauthors_m_gravatar").empty();
                        $("#topauthors_m").empty();
                        top_h = build_top_authors_head(top, 'lines changed');
                        $("#topauthors_m_gravatar").append(top_h);
                        if (top.length > 3) {
                            top_b = build_top_authors_body(top, 'tablc-dmore', limit);
                            $("#topauthors_m").append(top_b);
                            $('#tablc-dmore').click(function() {
                                limit = limit + 10;
                                fill_top_authors_by_lchanged(limit);
                            });
                        }
                    })
                    .fail(function(err) {
                        $("#topauthor-bylchanged-progress").empty();
                        $("#topauthors_m_gravatar").empty();
                        $("#topauthors_m").empty();
                        console.log(err);
                    });
            }
            fill_top_authors_by_lchanged(10);

        } else {
            $("#empty-warning").show();
            $("#infos-duration").hide();
            $("#infos-first_commit").hide();
            $("#infos-last_commit").hide();
            $("#top_authors_c_div").hide();
            $("#infos-authors_amount").hide();
            $("#commits_histo_div").hide();
            $("#contributors_histo_div").hide();
            $("#top_authors_c_div").hide();
            $("#top_authors_lc_div").hide();
            $("#commits_listing_div").hide();
            $("#top_authors_new").hide();
        }
    });
}

function contributors_page_init() {
    init_menu();

    function fill_resultinfos_gen(leaf) {
        $("#resultinfos").empty();
        $("#resultinfos").append(leaf);
    }
    function fill_resultinfos(ret) {
        var size = Object.keys(ret).length;
        $("#resultinfos").empty();
        $("#resultinfos").append(" - " + size + " results");
    }
    function fill_result(ret) {
        $("#search-results").empty();
        $.each(ret, function(k, v) {
            var box = '<div class="col-md-2"><div class="panel panel-default">' +
                '<div class="panel-heading"><h3 class="panel-title">' +
                '<span style="padding-right: 5px"><img src="https://www.gravatar.com/avatar/' +
                v.gravatar + '?s=20"></span>' +
                '<span><a href=contributor.html?cid=' +
                k + '>' + escapeHtml(v.name) + '</a></span></h3>' +
                '</div></div></div>';
            $("#search-results").append(box);
        });
    }

    $("#page-title").append("[RepoXplorer] - Search a contributor");

    $('#search-txt').bind("enterKey",function(e){
        var args = {};
        args['query'] = $("#search-txt").val();
        fill_resultinfos_gen('<span class="glyphicon glyphicon-refresh glyphicon-refresh-animate"></span>');
        $.getJSON("api/v1/search/search_authors", args)
            .done(
                function(data) {
                    fill_resultinfos(data);
                    fill_result(data);
                })
            .fail(
                function(err) {
                    fill_resultinfos_gen('Server side error');
                });
    });
    $('#search-txt').keyup(function(e){
      if(e.keyCode == 13) {
        $(this).trigger("enterKey");
    }
    });
}

function get_releases(pid, tid) {
    var args = {};
    args['pid'] = pid;
    args['tid'] = tid;
    args['inc_repos'] = getUrlParameter('inc_repos');

    var releases = [];
    $.getJSON("api/v1/tags/tags", args)
        .done(
            function(data) {
                data.sort(function(a, b){
                    if(a.date < b.date){ return 1;}
                    if(a.date > b.date){ return -1;}
                    return 0;
                });
                $.each(data, function(i, o) {
                    rdate = new Date(1000 * o.date);
                    rdate = moment(rdate);
                    if (o.repo == undefined) {
                      var text = rdate.format("YYYY-MM-DD") + " - " + o.name;
                    } else {
                      var text = rdate.format("YYYY-MM-DD") + " - " + o.name + " - " + o.repo;
                    }
                    $('#releases').append($('<option>', {
                        text: text,
                        value: rdate.format("YYYY-MM-DD")
                    }));
                });
            })
        .fail(
            function(err) {
                console.log(err);
            });
}

function get_metadata_keys(pid, tid, cid) {
    if ($('#inc_merge_commit').prop('checked')) {
        var inc_merge_commit = 'on';
    }

    var args = {};
    args['pid'] = pid;
    args['tid'] = tid;
    args['cid'] = cid;
    args['dfrom'] = getUrlParameter('dfrom');
    args['dto'] = getUrlParameter('dto');
    args['inc_merge_commit'] = inc_merge_commit;
    args['inc_repos'] = getUrlParameter('inc_repos');

    $('#metadata').append($('<option>', {
        text: 'Select a metadata key',
        value: ''
    }));
    $('#metadata-values').append($('<option>', {
        text: 'Select a metadata value',
        value: ''
    }));

    $('#metadata').on('change', function() {
        $('#metadata-values')
            .find('option')
            .remove()
            .end();
        if (this.value === '') {return 1;}
        args['key'] = this.value;
        $.getJSON("api/v1/metadata/metadata", args)
            .done(
                function(data) {
                    $('#metadata-values').append($('<option>', {
                        text: '*',
                        value: '*'
                    }));
                    $.each(data, function(i, v) {
                        $('#metadata-values').append($('<option>', {
                            text: v,
                            value: v
                        }));
                    });
                })
            .fail(
                function(err) {
                    console.log(err);
                });
    })

    $.getJSON("api/v1/metadata/metadata", args)
        .done(
            function(data) {
                var temp = [];
                $.each(data, function(key, value) {
                    temp.push({v:value, k: key});
                });
                temp.sort(function(a, b){
                    if(a.v < b.v){ return 1;}
                    if(a.v > b.v){ return -1;}
                    return 0;
                });
                $.each(temp, function(i, o) {
                    $('#metadata').append($('<option>', {
                        text: o.k,
                        value: o.k
                    }));
                });
            })
        .fail(
            function(err) {
                console.log(err);
            });
}

function get_commits(pid, tid, cid, gid, page, with_projects_c) {
    if (page === undefined) {
        page = 0;
    }
    if ($('#inc_merge_commit').prop('checked')) {
        var inc_merge_commit = 'on';
    }

    var args = {};
    args['pid'] = pid;
    args['tid'] = tid;
    args['cid'] = cid;
    args['gid'] = gid;
    args['start'] = page;
    args['dfrom'] = getUrlParameter('dfrom');
    args['dto'] = getUrlParameter('dto');
    args['inc_merge_commit'] = inc_merge_commit;
    args['inc_repos'] = getUrlParameter('inc_repos');
    args['metadata'] = getUrlParameter('metadata');
    args['exc_groups'] = getUrlParameter('exc_groups');
    args['inc_groups'] = getUrlParameter('inc_groups');

    $("#commits-table-progress").append(
        '&nbsp;<span class="glyphicon glyphicon-refresh glyphicon-refresh-animate"></span>');
    $.getJSON("api/v1/commits/commits", args).done(function(data) {
        $("#commits-table").empty();
        $("#commits-table-progress").empty();
        $("#commits-table").append("<table class=\"table table-striped\">");
        var theader = "<tr>";
        theader += "<th>Date of commit</th>";
        if (with_projects_c) {
            theader += "<th>Projects</th>";
        }
        theader += "<th>Repository refs</th>";
        theader += "<th>Author/Committer</th>";
        theader += "<th>Message</th>";
        theader += "<th>Changed lines</th>";
        theader += "<th>Time To Land</th>";
        theader += "</tr>";
        $("#commits-table table").append(theader);
        $.each( data[2], function(k, v) {
            var cmt_date = new Date(1000 * v['committer_date']);
            cmt_date = moment(cmt_date);
            var elm = "<tr>";
            if (with_projects_c) {
                var projects = "";
                $.each(v['projects'], function(i, p) {
                    if (i > 0) {projects += "<br>";}
                    projects += p;
                });
            }
            var refs = "";
            $.each(v['repos'], function(i, p) {
                if (i > 0) {refs += "<br>";}
                refs += p;
            });
            elm += "<td>" + cmt_date.format("MMM D, YYYY") + "</td>";
            if (with_projects_c) {
                elm += "<td>" + projects + "</td>";
            }
            elm += "<td>" + refs + "</td>";
            elm += "<td><span style='padding-right: 5px'><img src='https://www.gravatar.com/avatar/" +
                v['author_gravatar'] + "?s=20'></span><span><a href=contributor.html?cid=" +
                v['cid'] + ">" + escapeHtml(v['author_name']) + "</a></span>";
            if (v['ccid'] != v['cid']) {
                elm += "<br><span style='padding-right: 5px'><img src='https://www.gravatar.com/avatar/" +
                    v['committer_gravatar'] + "?s=20'></span><span><a href=contributor.html?cid=" +
                    v['ccid'] + ">" + escapeHtml(v['committer_name']) + "</a><span>";
            }
            elm += "</td>";
            // Just use the first gitweb link atm
            if (v['gitwebs'][0].length > 0) {
                elm += "<td><a href=" + v['gitwebs'][0] + ">" + v['commit_msg'] + "</a></td>";
            } else {
                elm += "<td>" + v['commit_msg'] + "</td>";
            }
            elm += "<td>" + v['line_modifieds'] + "</td>";
            elm += "<td>" + v['ttl'] + "</td>";
            elm += "</tr>";
            $("#commits-table table").append(elm);
        });
        $("#commits-table").append("</table>");
    })
        .fail(function(err) {
            $("#commits-table-progress").empty();
            console.log(err);
        });
}

function check_fragment() {
    var hash = window.location.hash || "#page-1";
    hash = hash.match(/^#page-(\d+)$/);
    if(hash) {
        page = parseInt(hash[1]);
        $("#pagination").pagination('selectPage', page);
    }
}

function install_paginator(pid, tid, cid, gid, items_amount, with_projects_c) {
    if (items_amount >= 1000) {
        // Limit the amount of pages to 100
        // User should use the calendar filter to dig in the results
        items_amount = 1000;
    }
    $(window).bind("popstate", check_fragment);
    $('#pagination').pagination({
        items: items_amount,
        itemsOnPage: 10,
        cssStyle: 'light-theme',
        onPageClick: function(pageNumber, ev) {
            // The paginator will update the page hash fragment
            // To avoid the double get_commits call (due to the bind of the popstate event)
            // I skip calling get_commit if ev is defined.
            // On hash change/history update the paginator is refresh
            // On click on a button the paginator is refresh
            if (!(ev)) {
                get_commits(pid, tid, cid, gid, (pageNumber - 1) * 10);
            }
        }
    });
}
