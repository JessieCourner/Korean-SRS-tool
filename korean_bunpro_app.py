                active = stats.get("active", 0) or 0
                guide = lesson_guide(lesson)
                with st.container(border=True):
                    left, right = st.columns([5, 1.3])
                    with left:
                        st.markdown(f"**Lesson {lesson['lesson_number']}: {lesson['title']}**")
                        if guide.get("available"):
                            st.caption(f"{lesson['pattern']} · {active}/{cards} cards active · HTSK guide inside Study")
                            st.markdown(f"[Open the full HTSK lesson ↗]({guide['source_url']})")
                        else:
                            st.caption("🔒 HTSK has not published this lesson yet")
                            st.markdown(f"[Open the official HTSK page ↗]({guide['source_url']})")
                    with right:
                        if guide.get("available"):
                            if st.button("Study", key=f"study_{lesson['id']}", use_container_width=True):
                                lesson_request = (lesson["id"], False)
    if lesson_request:
        render_lesson_dialog(*lesson_request)


def page_progress():
    st.title("Progress")
    data = rows("""
        SELECT lessons.unit, lessons.lesson_number, lessons.title,
               SUM(CASE WHEN reviews.retired=0 THEN 1 ELSE 0 END) AS cards,
               SUM(CASE WHEN reviews.retired=0 AND reviews.active=1 THEN 1 ELSE 0 END) AS active,
               SUM(CASE WHEN reviews.retired=0 AND reviews.level>=8 THEN 1 ELSE 0 END) AS mastered
        FROM lessons JOIN cards ON cards.lesson_id=lessons.id
        JOIN reviews ON reviews.card_id=cards.id
        GROUP BY lessons.id ORDER BY lessons.unit, lessons.lesson_number
    """)
    headers = ["Unit", "Lesson", "Title", "Cards", "Active", "Mastered"]
    body = []
    for row in data:
        body.append("<tr>" + "".join([
            f"<td>{row['unit']}</td>",
            f"<td>{row['lesson_number']}</td>",
            f"<td>{row['title']}</td>",
            f"<td>{row['cards'] or 0}</td>",
            f"<td>{row['active'] or 0}</td>",
            f"<td>{row['mastered'] or 0}</td>",
        ]) + "</tr>")
    table = "<div class='chibi-table-wrap'><table class='chibi-table'><thead><tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr></thead><tbody>" + "".join(body) + "</tbody></table></div>"
    st.markdown(table, unsafe_allow_html=True)


def page_shop():
    st.title("Crystal Shop ✨")
    st.markdown(f"<div class='cute-note'>💎 You have <b>{crystals()} crystals</b></div>", unsafe_allow_html=True)
    st.write("Earn crystals by studying and reviewing. Buy a cute companion or a new study-room design.")
    categories = [("Faces", "face", "Choose your study buddy"), ("Characters", "character", "A little friend for your dashboard"), ("Room designs", "design", "Change the mood of your study room"), ("Card frames", "frame", "Decorate your Review screen"), ("Progress trackers", "tracker", "Choose how your progress grows")]
    tabs = st.tabs([f"{name}  ✨" for name, _, _ in categories])
    for tab, (name, kind, subtitle) in zip(tabs, categories):
        with tab:
            st.subheader(name)
            st.caption(subtitle)
            items = rows("SELECT * FROM shop_items WHERE kind=? ORDER BY price, id", (kind,))
            for item in items:
                owned = one("SELECT 1 FROM inventory WHERE item_id=?", (item["id"],))
                active_key = f"active_{item['kind']}"
                is_active = setting(active_key, "") == item["id"]
                with st.container(border=True):
                    left, middle, right = st.columns([1, 4, 1.5])
                    with left:
                        st.markdown(f"<div class='shop-item-icon'>{item['icon']}</div>", unsafe_allow_html=True)
                    with middle:
                        st.markdown(f"### {item['name']}")
                        st.caption(item["description"])
                        if kind == "frame":
                            style = FRAME_STYLES.get(item["id"], FRAME_STYLES["frame_sakura"])
                            st.markdown(
                                f'''<div style="border:3px solid {style['border']};border-radius:18px;padding:9px 12px;background:{style['background']};color:#684d7b;text-align:center;font-weight:800">{style['decor']} Review card preview · {style['decor']}</div>''',
                                unsafe_allow_html=True,
                            )
                        elif kind == "tracker":
                            st.markdown(
                                f'''<div class="quest-track" style="margin:7px 0 4px"><div class="quest-fill" style="width:55%;background:{TRACKER_COLORS.get(item['id'], '#f5a6c8')}"></div><div class="progress-mascot" style="left:clamp(0px,calc(55% - 19px),calc(100% - 38px))">{item['icon']}</div></div>''',
                                unsafe_allow_html=True,
                            )
                    with right:
                        if is_active:
                            st.success("Active")
                        elif owned:
                            if st.button("Use", key=f"use_{item['id']}", use_container_width=True):
                                buy_or_activate(item["id"]); st.rerun()
                        elif st.button(f"Buy · {item['price']} 💎", key=f"buy_{item['id']}", use_container_width=True):
                            if buy_or_activate(item["id"]):
                                st.success("Purchased!")
                                st.rerun()
                            else:
                                st.error("Not enough crystals yet.")


bootstrap_app_data(CONTENT_SYNC_VERSION)
if st.session_state.pop("go_review", False):
    st.session_state["nav"] = "Review"
pending_mobile_page = st.session_state.pop("mobile_nav_target", None)
if pending_mobile_page in NAV_PAGES:
    st.session_state["nav"] = pending_mobile_page
render_mobile_navigation()
render_bts_motivation()
st.sidebar.markdown('<div class="brand-logo"><div class="brand-mark">🍡</div><div><div class="brand-name">Mochi Hangul</div><div class="brand-subtitle">Korean grammar SRS</div></div></div>', unsafe_allow_html=True)
page = st.sidebar.radio("Navigate", list(NAV_PAGES), key="nav")
st.sidebar.markdown(f"💎 **{crystals()} crystals**")
if page == "Review":
    # Sidebar navigation enters Review without going through the Dashboard's
    # button callback. Start one queue snapshot for that visit as well.
    if not st.session_state.get("_review_page_active", False):
        start_review_session()
        st.session_state["_review_page_active"] = True
else:
    st.session_state["_review_page_active"] = False
if page == "Dashboard": page_dashboard()
elif page == "Review": render_review_dialog()
elif page == "Lessons": page_lessons()
elif page == "Progress": page_progress()
else: page_shop()
