const I18N = {
  en: {
    pageTitle: "GTU Schedule Finder",
    heroBadge: "Georgian Technical University",
    heroTitle: "Find your lectures",
    heroSubtitle:
      'Search by your lecturer\'s name. Data is fetched live from <a href="http://leqtori.gtu.ge/" target="_blank" rel="noopener">leqtori.gtu.ge</a> — weekly timetables and final exam schedules.',
    searchLabel: "Lecturer name",
    searchPlaceholder: "e.g. Gratiashvili, გრატიაშვილი, or Milashvili",
    searchBtn: "Search",
    filterWeekly: "Weekly timetable",
    filterExams: "Final exams",
    footerTip1:
      "Tip: Georgian names often appear as <em>Surname Firstname</em>. You can search in Georgian, English, or Russian.",
    footerTip2: "Timetables auto-update every Saturday from leqtori.gtu.ge — no manual refresh needed.",
    langEn: "English",
    langKa: "Georgian",
    langRu: "Russian",

    badgeWeekly: "Weekly class",
    badgeExam: "Final exam",
    labelLecturer: "Lecturer",
    labelDay: "Day",
    labelDate: "Date",
    labelTime: "Time",
    labelRoom: "Room",
    labelGroup: "Group",
    labelFaculty: "Faculty",
    dash: "—",

    emptyTitle: 'No schedule entries found for <strong>{query}</strong>.',
    emptyHint: "Try the lecturer's surname in Georgian or English.",
    statusSearching: "Searching…",
    statusStillLoading: "Still loading GTU data — please wait a moment and try again.",
    statusFound: 'Found {count} result for "{query}"',
    statusFoundPlural: 'Found {count} results for "{query}"',
    statusSearchFailed: "Search failed",
    statusSomethingWrong: "Something went wrong.",
    statusLoading: "Loading GTU timetable data…",
    statusUpdating:
      "Schedule files are being updated — this can take up to 5 minutes. Search is still available using last week's data.",
    statusReady: "Ready — {teachers} lecturers, {weekly} weekly classes, {exam} exam slots.",
    statusReadyUpdated: " Data from {date}. Updates automatically every Saturday.",
    statusWarnings: " ({count} source warning)",
    statusWarningsPlural: " ({count} source warnings)",
    statusWaiting: "Waiting for schedule data…",
    statusServerError:
      "Could not reach the server. On Render free tier, wait ~30s for the site to wake up, then reload the page.",
  },

  ka: {
    pageTitle: "GTU განრიგის ძებნა",
    heroBadge: "საქართველოს ტექნიკური უნივერსიტეტი",
    heroTitle: "იპოვე შენი ლექციები",
    heroSubtitle:
      'მოძებნე ლექტორის სახელით. მონაცემები პირდაპირ <a href="http://leqtori.gtu.ge/" target="_blank" rel="noopener">leqtori.gtu.ge</a>-დან — კვირეული განრიგი და საბოლოო გამოცდები.',
    searchLabel: "ლექტორის სახელი",
    searchPlaceholder: "მაგ. გრატიაშვილი, Gratiashvili, Milashvili",
    searchBtn: "ძებნა",
    filterWeekly: "კვირეული განრიგი",
    filterExams: "საბოლოო გამოცდები",
    footerTip1:
      "რჩევა: ხშირად სახელი ფორმატითაა <em>გვარი სახელი</em>. შეგიძლია ქართულად, ინგლისურად ან რუსულად მოძებნო.",
    footerTip2: "განრიგი ავტომატურად განახლდება ყოველ შაბათს leqtori.gtu.ge-დან — ხელით განახლება არ სჭირდება.",
    langEn: "English",
    langKa: "ქართული",
    langRu: "Русский",

    badgeWeekly: "კვირეული",
    badgeExam: "გამოცდა",
    labelLecturer: "ლექტორი",
    labelDay: "დღე",
    labelDate: "თარიღი",
    labelTime: "დრო",
    labelRoom: "აუდიტორია",
    labelGroup: "ჯგუფი",
    labelFaculty: "ფაკულტეტი",
    dash: "—",

    emptyTitle: '<strong>{query}</strong>-ისთვის განრიგი ვერ მოიძებნა.',
    emptyHint: "სცადე ლექტორის გვარი ქართულად ან ინგლისურად.",
    statusSearching: "ძებნა…",
    statusStillLoading: "მონაცემები ჯერ იტვირთება — გთხოვ, ცოტა დაელოდე და სცადე თავიდან.",
    statusFound: 'ნაპოვნია {count} შედეგი "{query}"-ისთვის',
    statusFoundPlural: 'ნაპოვნია {count} შედეგი "{query}"-ისთვის',
    statusSearchFailed: "ძებნა ვერ მოხერხდა",
    statusSomethingWrong: "რაღაც შეცდომა მოხდა.",
    statusLoading: "GTU განრიგის მონაცემები იტვირთება…",
    statusUpdating:
      "განრიგი განახლდება — ეს 5 წუთამდე შეიძლება გაგრძელდეს. ძებნა მაინც მუშაობს ბოლო კვირის მონაცემებით.",
    statusReady: "მზადაა — {teachers} ლექტორი, {weekly} კვირეული, {exam} გამოცდა.",
    statusReadyUpdated: " მონაცემები {date}-დან. ავტომატურად განახლდება ყოველ შაბათს.",
    statusWarnings: " ({count} გაფრთხილება)",
    statusWarningsPlural: " ({count} გაფრთხილება)",
    statusWaiting: "განრიგის მონაცემების მოლოდინი…",
    statusServerError:
      "სერვერთან დაკავშირება ვერ მოხერხდა. Render-ის უფასო გეგმაზე ~30 წამი დაელოდე და გვერდი თავიდან ჩატვირთე.",
  },

  ru: {
    pageTitle: "GTU — поиск расписания",
    heroBadge: "Грузинский технический университет",
    heroTitle: "Найдите свои лекции",
    heroSubtitle:
      'Поиск по имени преподавателя. Данные загружаются с <a href="http://leqtori.gtu.ge/" target="_blank" rel="noopener">leqtori.gtu.ge</a> — недельное расписание и финальные экзамены.',
    searchLabel: "Имя преподавателя",
    searchPlaceholder: "напр. Gratiashvili, გრატიაშვილი или Milashvili",
    searchBtn: "Найти",
    filterWeekly: "Недельное расписание",
    filterExams: "Финальные экзамены",
    footerTip1:
      "Подсказка: грузинские имена часто в формате <em>Фамилия Имя</em>. Можно искать на грузинском, английском или русском.",
    footerTip2: "Расписание обновляется каждую субботу с leqtori.gtu.ge — ручное обновление не требуется.",
    langEn: "English",
    langKa: "ქართული",
    langRu: "Русский",

    badgeWeekly: "Недельное",
    badgeExam: "Экзамен",
    labelLecturer: "Преподаватель",
    labelDay: "День",
    labelDate: "Дата",
    labelTime: "Время",
    labelRoom: "Аудитория",
    labelGroup: "Группа",
    labelFaculty: "Факультет",
    dash: "—",

    emptyTitle: 'Расписание для <strong>{query}</strong> не найдено.',
    emptyHint: "Попробуйте фамилию преподавателя на грузинском или английском.",
    statusSearching: "Поиск…",
    statusStillLoading: "Данные ещё загружаются — подождите немного и попробуйте снова.",
    statusFound: 'Найдено {count} результат для «{query}»',
    statusFoundPlural: 'Найдено {count} результатов для «{query}»',
    statusSearchFailed: "Ошибка поиска",
    statusSomethingWrong: "Что-то пошло не так.",
    statusLoading: "Загрузка расписания GTU…",
    statusUpdating:
      "Расписание обновляется — это может занять до 5 минут. Поиск доступен по данным прошлой недели.",
    statusReady: "Готово — {teachers} преподавателей, {weekly} занятий, {exam} экзаменов.",
    statusReadyUpdated: " Данные от {date}. Обновляется каждую субботу автоматически.",
    statusWarnings: " ({count} предупреждение)",
    statusWarningsPlural: " ({count} предупреждений)",
    statusWaiting: "Ожидание данных расписания…",
    statusServerError:
      "Не удалось связаться с сервером. На бесплатном Render подождите ~30 сек и перезагрузите страницу.",
  },
};

const LANG_STORAGE_KEY = "gtu-schedule-lang";
const SUPPORTED_LANGS = ["en", "ka", "ru"];

let currentLang = (() => {
  const saved = localStorage.getItem(LANG_STORAGE_KEY);
  return SUPPORTED_LANGS.includes(saved) ? saved : "en";
})();

const DAY_NAMES = {
  en: {
    Monday: "Monday",
    Tuesday: "Tuesday",
    Wednesday: "Wednesday",
    Thursday: "Thursday",
    Friday: "Friday",
    Saturday: "Saturday",
    Sunday: "Sunday",
  },
  ka: {
    Monday: "ორშაბათი",
    Tuesday: "სამშაბათი",
    Wednesday: "ოთხშაბათი",
    Thursday: "ხუთშაბათი",
    Friday: "პარასკევი",
    Saturday: "შაბათი",
    Sunday: "კვირა",
  },
  ru: {
    Monday: "Понедельник",
    Tuesday: "Вторник",
    Wednesday: "Среда",
    Thursday: "Четверг",
    Friday: "Пятница",
    Saturday: "Суббота",
    Sunday: "Воскресенье",
  },
};

function translateDay(day) {
  if (!day) return t("dash");
  const map = DAY_NAMES[currentLang] || DAY_NAMES.en;
  return map[day] || day;
}

function t(key, params = {}) {
  const bundle = I18N[currentLang] || I18N.en;
  let str = bundle[key] ?? I18N.en[key] ?? key;
  for (const [k, v] of Object.entries(params)) {
    str = str.replaceAll(`{${k}}`, String(v));
  }
  return str;
}

function getLang() {
  return currentLang;
}

function setLang(lang) {
  if (!SUPPORTED_LANGS.includes(lang)) return;
  currentLang = lang;
  localStorage.setItem(LANG_STORAGE_KEY, lang);
  document.documentElement.lang = lang === "ka" ? "ka" : lang === "ru" ? "ru" : "en";
  document.title = t("pageTitle");
  applyStaticTranslations();
  updateLangButtons();
  window.dispatchEvent(new CustomEvent("languagechange"));
}

function applyStaticTranslations() {
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.dataset.i18n;
    if (key) el.innerHTML = t(key);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    el.placeholder = t(el.dataset.i18nPlaceholder);
  });
  document.querySelectorAll("[data-i18n-title]").forEach((el) => {
    el.title = t(el.dataset.i18nTitle);
  });
}

function updateLangButtons() {
  document.querySelectorAll("[data-lang]").forEach((btn) => {
    const active = btn.dataset.lang === currentLang;
    btn.classList.toggle("active", active);
    btn.setAttribute("aria-pressed", active ? "true" : "false");
  });
}

applyStaticTranslations();
updateLangButtons();
