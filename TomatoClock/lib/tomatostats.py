# -*- coding: utf-8 -*-
# Created: 3/13/2018
# Project : TomatoClock
import datetime
import json
from operator import itemgetter

trans = {
    'TOMATO COLOCK': {'zh_CN': u'番茄时钟', 'en': u'Tomato Clock'},
    'report days part1': {'zh_CN': u'最近番茄时钟数据：', 'en': u'Recent Tomato Clock statistics：'},
    'days': {'zh_CN': u'天', 'en': u'day(s)'},
    "'Minutes Studied'": {'zh_CN': u"'学习分钟数'", 'en': u"'Minutes Studied'"},
    "'Best Focus Hour'": {'zh_CN': u"'最佳学习时段'", 'en': u"'Best Focus Hour'"},
    "'Count of Tomatoes and Minutes'": {'zh_CN': u"'番茄和学习分钟'",
                                        'en': u"'Count of Tomatoes and Minutes'"},
    "'Tomato Count'": {'zh_CN': u"'番茄个数'", 'en': u"'Tomato Count'"},
    "'Productivity'": {'zh_CN': u"'卡片/番茄'", 'en': u"'Cards/Tomato'"},
    "'{a} <br/>{b} Clock: {c} Minutes'": {'zh_CN': u"'{a} <br/>{b} 点: {c} 分钟'",
                                          'en': u"'{a} <br/>{b} Clock: {c} Minutes'"},

    "total_studied_hour": {'zh_CN': u'总时间（小时）', 'en': u'Total Time (Hour)'},
    "total_tomato": {'zh_CN': u'总番茄钟', 'en': u'Total Tomato'},
    "today_total_min": {'zh_CN': u'今日时间（分钟）', 'en': u'Today Time (Minute)'},
    "today_total_tomato": {'zh_CN': u'今日番茄钟', 'en': u'Today Tomato'},
    "today_min_pctg": {'zh_CN': u'今日时间完成率', 'en': u'Today Time %'},
    "today_tomato_pctg": {'zh_CN': u'今日番茄完成率', 'en': u'Today Tomato %'}

}


def _(key):
    from anki.lang import currentLang
    lang = currentLang
    key = key.upper().strip()
    if lang != 'zh_CN' and lang != 'en' and lang != 'fr':
        lang = 'en'  # fallback

    def disp(s):
        return s.lower().capitalize()

    for k, v in trans.items():
        trans[k.upper()] = v

    if key not in trans or lang not in trans[key]:
        return disp(key)
    return trans[key][lang]


class TomatoStats:
    def __init__(self, db, debug=False, user_config=None):
        self.debug = debug
        self.user_config = user_config
        if self.debug:
            from .db import TomatoDB
            assert isinstance(db, TomatoDB)
        self.db = db
        self._data_by_dates = []
        self._recent_days = None

    def reports(self, recent_days):
        self._recent_days = recent_days

        reports_js = [
            self._chart_tomato_cnt(),
            self._chart_tomato_hour(),
            self._chart_study_minute(),
            self._chart_cards_per_tomato_cnt()
        ]
        if any(reports_js):
            (total_studied_hour, total_tomato, today_total_min, today_total_tomato,
             today_min_pctg, today_tomato_pctg) = self._numbers()

            summary_table_html = """
            <table  class=summary>
            <tr>
                <td class="summary_td">
                    <span class="summary_val">%(total_studied_hour_val)s</span>
                    <br>
                    <span class="summary_lb">%(total_studied_hour)s</span>  
                </td>
                <td class="summary_td">
                    <span class="summary_val">%(today_total_min_val)s</span>
                    <br>
                    <span class="summary_lb">%(today_total_min)s</span>
                </td>
                <td class="summary_td">
                    <span class="summary_val">%(today_min_pctg_val)s</span>
                    <br>
                    <span class="summary_lb">%(today_min_pctg)s</span>
                </td>
                
                <td class="summary_td">
                    <span class="summary_val">%(total_tomato_val)s</span>
                    <br>
                    <span class="summary_lb">%(total_tomato)s</span>
                </td>
                <td class="summary_td">
                    <span class="summary_val">%(today_total_tomato_val)s</span>
                    <br>
                    <span class="summary_lb">%(today_total_tomato)s</span>
                </td>
                <td class="summary_td">
                    <span class="summary_val">%(today_tomato_pctg_val)s</span>
                    <br>
                    <span class="summary_lb">%(today_tomato_pctg)s</span>
                </td>
            </tr>
            </table>
            """ % dict(
                total_studied_hour=_("total_studied_hour"),
                total_tomato=_("total_tomato"),
                today_total_min=_("today_total_min"),
                today_total_tomato=_("today_total_tomato"),
                today_min_pctg=_("today_min_pctg"),
                today_tomato_pctg=_("today_tomato_pctg"),

                total_studied_hour_val=total_studied_hour,
                total_tomato_val=total_tomato,
                today_total_min_val=today_total_min,
                today_total_tomato_val=today_total_tomato,
                today_min_pctg_val=today_min_pctg,
                today_tomato_pctg_val=today_tomato_pctg
            )

            days = [7, 14, 30, 60, 180] if not self.user_config else self.user_config.report_recent_days
            html = u"""
            <style>
                * {
                    font-family: 'Microsoft YaHei UI', Consolas, serif;
                }
            
                .summary_td {
                    text-align: center;
                    font-family: 'Microsoft YaHei UI', Consolas, serif;
                }
            
                .summary_val {
                    font-weight: bold;
                    font-size: large;
                }
            
                .summary_lb {
                    font-size: smaller;
                }
            
                .summary td {
                    /*border: 1px solid #ed1c40;*/
                    padding: 0 20px 20px 0;
                    border-radius: .25rem;
                    border-spacing: 0;
                }
            
                .summary {
                    
                }
            </style>
            %s
            <hr>
            <table width=95%% align=center>
                <tr>
                    <td align=center colspan=2> 
                        %s
                    </td>
                </tr>
                <tr>
                    <td width=300px height=300px id=tomato_cnt align=center></td>
                    <td width=300px height=300px id=cards_per_tomato_cnt align=center></td>
                </tr>
                <tr >
                    <td width=300px height=300px id=study_minute align=center></td>
                    <td width=600px height=300px id=tomato_hour align=center></td>
                </tr>
                <tr>
                    <td align=left colspan=2> 
                        <div>%s <select id=recent_days onchange="sel_Change()">
                          %s
                        </select> %s</div>
                    </td>
                </tr>
            </table>
            <script>
            function sel_Change(){
                var objS = document.getElementById("recent_days");
                var days = objS.options[objS.selectedIndex].value;
                py.link('report_refresh' + days)
            }
            </script>
            <hr>
            %s
            """
            return_val = html % (self._js_ref,

                                 summary_table_html,

                                 _("report days part1"),
                                 u"".join(
                                     [u'<option value=%(days)s '
                                      u'%(selected)s>%(days)s</option>' % dict(days=i,
                                                                               selected="selected='selected'"
                                                                               if i == self._recent_days else '')
                                      for i in
                                      days]
                                 ),
                                 _("days"),

                                 u"""
                                  <script>
                                  {}
                                  </script>
                                  """.format(u"".join(reports_js)),

                                 )
            # set default selection
            # document.getElementById("sel")[2].selected = true;
            return return_val
        return ''

    @property
    def _js_ref(self):
        return u"""
        <script src="http://echarts.baidu.com/examples/vendors/echarts/echarts.min.js"></script>
        """

    def _graph(self, id, conf):
        id = unicode(id, encoding="utf-8")
        html = u"""
        echarts.init(document.getElementById('%(id)s')).setOption(%(conf)s);
        """ % dict(id=id, conf=json.dumps(conf).replace("\"", ""))
        return html

    @property
    def report_days(self):
        return (datetime.datetime.now() + datetime.timedelta(days=-7)).date()

    def data_by_dates(self):
        if not self._data_by_dates:
            _list_data = self.db.execute(
                """
                SELECT
                  TOMATO_DT,
                  sum(TOMATO_MINS) TT_TOMATO_MINS,
                  sum(TARGET_MINS) TT_TGT_MINS,
                  sum(TOMATO_CNT)  TT_TOMATO_CNT,
                  sum(CARDS_CNT)   TT_CARDS_COUNT,
                  sum(COMPLETE_TOMATO_CNT) TT_CMP_TOMATO_CNT,
                  count(COMPLETE_TOMATO_CNT) TT_TRIED_TOMATO_CNT
                FROM (SELECT
                        strftime('%m/%d', ts.tomato_dt)                                                    TOMATO_DT,
                        (strftime('%s', ts.ended) - strftime('%s', ts.started)) / 60.0                     TOMATO_MINS,
                        ts.target_secs / 60.0                                                              TARGET_MINS,
                        (strftime('%s', ts.ended) - strftime('%s', ts.started)) / round(ts.target_secs, 1) TOMATO_CNT,
                        (SELECT count(*)
                         FROM tomato_session_item tsi
                         WHERE ts.id = tsi.session_id)                                                     CARDS_CNT,
                         round((strftime('%s', ts.ended) - strftime('%s', ts.started)), 2) >= ts.target_secs COMPLETE_TOMATO_CNT
                      FROM tomato_session ts
                      WHERE ended IS NOT NULL 
                              AND date(ts.tomato_dt) >= ?
                              AND ts.deck = ?)
                GROUP BY TOMATO_DT
                """, self.report_days, self.db.deck['id']).fetchall()

            if not _list_data:
                self._data_by_dates = [[], [], [], [], []]

            x_dt_labels = ["'%s'" % i[0] for i in _list_data]
            y_tomato_min = [round(i[1], 2) for i in _list_data]
            y_tomato_target_min = [round(i[2], 2) for i in _list_data]
            y_tomato_count = [round(i[3], 2) for i in _list_data]
            y_cards_count = [round(i[4], 2) for i in _list_data]
            cmp_tomato_cnt = [round(i[5], 2) for i in _list_data]
            tried_tomato_cnt = [round(i[6], 2) for i in _list_data]

            self._data_by_dates = [x_dt_labels, y_tomato_count,
                                   y_tomato_min, y_tomato_target_min,
                                   y_cards_count, cmp_tomato_cnt, tried_tomato_cnt]
        return self._data_by_dates

    def _chart_study_minute(self, ):
        (x_dt_labels, y_tomato_count,
         y_tomato_min, y_tomato_target_min, y_cards_count, cmp_tomato_cnt, tried_tomato_cnt
         ) = self.data_by_dates()
        if not x_dt_labels:
            return ''

        conf = dict(
            tooltip=dict(
                trigger="'item'",
            ),
            title={
                "subtext": _("'Minutes Studied'")
            },
            xAxis=dict(data=x_dt_labels),
            yAxis={},
            series=[
                dict(
                    name=_("'Minutes Studied'"),
                    type=u"'bar'",
                    data=y_tomato_min
                )
            ]
        )

        return self._graph("study_minute", conf)

    def _chart_tomato_cnt(self, ):
        (x_dt_labels, y_tomato_count,
         y_tomato_min, y_tomato_target_min, y_cards_count, cmp_tomato_cnt, tried_tomato_cnt
         ) = self.data_by_dates()
        if not x_dt_labels:
            return ''

        conf = dict(
            tooltip=dict(
                trigger="'item'",
            ),
            title={
                "subtext": _("'Tomato Count'")
            },
            xAxis=dict(data=x_dt_labels),
            yAxis={},
            series=[
                dict(
                    name=_("'Tomato Count'"),
                    type=u"'bar'",
                    data=y_tomato_count
                )
            ]
        )

        return self._graph("tomato_cnt", conf)

    def _chart_cards_per_tomato_cnt(self):
        (x_dt_labels, y_tomato_count,
         y_tomato_min, y_tomato_target_min, y_cards_count, cmp_tomato_cnt, tried_tomato_cnt
         ) = self.data_by_dates()

        if not x_dt_labels:
            return ''

        try:
            y_cards_per_tomato = [round(a / b, 2) for a, b in zip(y_cards_count, y_tomato_count)]
        except ZeroDivisionError:
            y_cards_per_tomato = 0

        conf = dict(
            tooltip=dict(
                trigger="'item'",
            ),
            title={
                "subtext": _("'Productivity'")
            },
            xAxis=dict(type="'category'",
                       data=x_dt_labels),
            yAxis=dict(type="'value'"),
            series=[dict(
                name=_("'Productivity'"),
                data=y_cards_per_tomato,
                type="'line'",
                smoth=True), ]
        )

        return self._graph("cards_per_tomato_cnt", conf)

    def _chart_tomato_hour(self):
        _list_data = self.db.execute(
            """
            SELECT
              strftime('%H',ts.started)                 HOUR,
             round( sum((strftime('%s', ts.ended) - strftime('%s', ts.started)) / 60.0 ),2) MINS
            FROM tomato_session ts
            WHERE ended IS NOT NULL 
                  AND ts.tomato_dt >= ?
                  AND ts.deck = ?
            GROUP BY strftime('%H',ts.started)
            ORDER BY strftime('%H',ts.started)
            """, self.report_days, self.db.deck['id']).fetchall()

        if not _list_data:
            return ''

        _list_data = sorted(_list_data, key=itemgetter(0))
        time_slots = [
            '00:00 - 07:59',
            '08:00 - 10:59',
            '11:00 - 13:59',
            '14:00 - 16:59',
            '17:00 - 21:59',
            '21:00 - 23:59',
        ]
        time_slots_range = [
            (0, 7),
            (8, 11),
            (11, 14),
            (14, 17),
            (17, 21),
            (21, 24),
        ]

        mins_stutied = [0] * time_slots.__len__()
        for i, val in enumerate(_list_data):
            min = val[1]
            for slot_i, time_slot_rng in enumerate(time_slots_range):
                if time_slot_rng[0] <= int(val[0]) < time_slot_rng[1]:
                    mins_stutied[slot_i] = mins_stutied[slot_i] + round(min, 2)

        conf = dict(
            tooltip=dict(
                trigger="'item'",
                formatter=_("'{a} <br/>{b} Clock: {c} Minutes'")
            ),
            title={
                # "text": "'Count of Tomatoes and Minutes'",
                "subtext": _("'Best Focus Hour'")
            },
            xAxis=dict(type="'category'",
                       data=["'%s'" % i for i in time_slots]),
            yAxis=dict(type="'value'"),
            series=[dict(
                name=_("'Best Focus Hour'"),
                data=mins_stutied,
                type="'line'",
                areaStyle={}), ]
        )
        return self._graph("tomato_hour", conf)

    def _numbers(self):
        (x_dt_labels, y_tomato_count,
         y_tomato_min, y_tomato_target_min, y_cards_count, cmp_tomato_cnt, tried_tomato_cnt
         ) = self.data_by_dates()

        total_studied_hour = round(sum(y_tomato_min) / 60.0, 2)
        total_tomato = int(sum(cmp_tomato_cnt))

        if y_tomato_min:
            today_total_min = round(y_tomato_min[-1], 2)
        else:
            today_total_min = 0
        if cmp_tomato_cnt:
            today_total_tomato = int(cmp_tomato_cnt[-1])
        else:
            today_total_tomato = 0

        if y_tomato_target_min:
            _today_targets = round(y_tomato_target_min[-1], 2)
        else:
            _today_targets = 0
        if _today_targets:
            today_min_pctg = u"{}%".format(round(today_total_min / _today_targets, 4) * 100)
        else:
            today_min_pctg = u"0.00%"
        if tried_tomato_cnt and tried_tomato_cnt[-1]:
            today_tomato_pctg = u"{}%".format(round(today_total_tomato / tried_tomato_cnt[-1], 4) * 100)
        else:
            today_tomato_pctg = u"0.00%"
        return (total_studied_hour, total_tomato, today_total_min, today_total_tomato,
                today_min_pctg, today_tomato_pctg)
