import BLACKLIST_PHRASES from './utils/blacklist.js';
import React, { useEffect, useState, useCallback } from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import "./index.css";
import movies from './data/movies.json';
import theaters from './data/theaters.json';
import { getPosterUrl } from './utils/tmdb';
import POSTER_OVERRIDES from './utils/posterOverrides.json';

function normalizeDate(dateStr) {
  const match = dateStr.match(/^(\w{3})\s0?(\d{1,2})$/);
  if (match) {
    return `${match[1]} ${parseInt(match[2], 10)}`;
  }
  return dateStr;
}

function normalizeTitle(title) {
  let cleanedTitle = title;
  for (const phrase of BLACKLIST_PHRASES) {
    const regex = new RegExp(phrase, 'gi');
    cleanedTitle = cleanedTitle.replace(regex, '').trim();
  }
  return cleanedTitle.toLowerCase().replace(/[^\w\s]/g, '').replace(/\s+/g, ' ').trim();
}

const groupedByDateAndTitle = movies.reduce((acc, movie) => {
  const normTitle = normalizeTitle(movie.title);
  const normDate = normalizeDate(movie.date);
  if (!acc[normDate]) acc[normDate] = {};
  if (!acc[normDate][normTitle]) acc[normDate][normTitle] = [];
  let theaterEntry = acc[normDate][normTitle].find(m => m.theaterID === movie.theaterID);
  if (!theaterEntry) {
    acc[normDate][normTitle].push({
      ...movie,
      date: normDate,
      times: [{ time: movie.time, status: movie.status }]
    });
  } else {
    theaterEntry.times.push({ time: movie.time, status: movie.status });
  }
  return acc;
}, {});

const theaterMap = Object.fromEntries(theaters.map(t => [t.theaterID, t]));

function Modal({ title, onClose, children }) {
  return (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-80 flex justify-center items-center">
      <div className="bg-zinc-800 text-white rounded-2xl shadow-xl p-6 max-w-xl w-full relative max-h-[80vh] overflow-y-auto">
        <button onClick={onClose} className="absolute top-2 right-2 text-white text-2xl">×</button>
        <h2 className="text-2xl mb-4 font-bungee text-center">{title}</h2>
        {children}
      </div>
    </div>
  );
}

export default function App() {
  const [posters, setPosters] = useState({});
  const [selectedStack, setSelectedStack] = useState(null); // {date, title, idx}
  const [showTheaterList, setShowTheaterList] = useState(false);
  const [showMovieList, setShowMovieList] = useState(false);
  const [showOfflineList, setShowOfflineList] = useState(false);
  const [showCalendar, setShowCalendar] = useState(false);
  const [calendarDate, setCalendarDate] = useState(null);

  const getFirstTime = (movie) => {
    if (!movie.times || movie.times.length === 0) return '23:59';
    return movie.times[0].time;
  };

  const handleImageError = useCallback((e) => {
    if (!e.target.getAttribute('data-error-handled')) {
      e.target.src = '/posters/placeholder.webp';
      e.target.setAttribute('data-error-handled', 'true');
    }
  }, []);

  useEffect(() => {
    const loadPosters = async () => {
      const results = {};
      const seen = new Set();
      for (const movie of movies) {
        const normTitle = normalizeTitle(movie.title);
        const key = `${normTitle}|${movie.theaterID}`;
        if (!seen.has(key)) {
          seen.add(key);
          const url = await getPosterUrl(movie.title, movie.theaterID);
          if (url) results[normTitle] = url;
        }
      }
      setPosters(results);
    };
    if (process.env.NODE_ENV !== 'production') {
      loadPosters();
    } else {
      const staticPosters = {};
      for (const movie of movies) {
        const normTitle = normalizeTitle(movie.title);
        const override = POSTER_OVERRIDES.find(o => normalizeTitle(o.title) === normTitle);
        if (override?.file) {
          staticPosters[normTitle] = `/fixed_posters/${override.file}`;
        } else {
          staticPosters[normTitle] = `/posters/${normTitle.replace(/\s+/g, '_')}.webp`;
        }
      }
      setPosters(staticPosters);
    }
  }, []);

  const uniqueMovieKeys = new Set(movies.map(m => `${normalizeTitle(m.title)}|${m.theaterID}`));
  const uniqueMovies = Array.from(
    movies.reduce((acc, m) => {
      const norm = normalizeTitle(m.title);
      if (!acc.has(norm)) acc.set(norm, m.title);
      return acc;
    }, new Map()).values()
  );
  const offlineTheaters = theaters.filter(theater => theater.online === false);
  const availableDates = Object.keys(groupedByDateAndTitle).sort((a, b) => {
    const parse = (s) => {
      const m = s.match(/^(\w{3})\s(\d{1,2})$/);
      if (!m) return [0, 0];
      const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
      return [months.indexOf(m[1]), parseInt(m[2], 10)];
    };
    const [ma, da] = parse(a);
    const [mb, db] = parse(b);
    return ma !== mb ? ma - mb : da - db;
  });

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const scrollToDate = (date) => {
    const section = document.getElementById(`date-${date}`);
    if (section) {
      const yOffset = -90;
      const y = section.getBoundingClientRect().top + window.pageYOffset + yOffset;
      window.scrollTo({ top: y, behavior: 'smooth' });
    }
  };

  useEffect(() => {
    if (calendarDate) {
      const formatted = calendarDate.toISOString().split("T")[0];
      scrollToDate(formatted);
      setShowCalendar(false);
    }
  }, [calendarDate]);

  return (
    <>
      <header className="w-full bg-zinc-800 shadow-md sticky top-0 z-50">
        <div className="sm:hidden px-4 py-4">
          <h1 className="text-4xl font-bold text-center text-white font-bungee border-b border-zinc-600 pb-2">
            🎬 DC Kino Showtimes
          </h1>
          <div className="flex w-full px-4 mt-3 gap-4">
            <button className="text-white material-icons text-base flex-1" onClick={scrollToTop}>cottage</button>
            <button className="text-white material-icons text-base flex-1" onClick={() => setShowCalendar(true)}>calendar_month</button>
          </div>
        </div>
        <div className="hidden sm:flex justify-between items-center px-4 py-4">
          <button className="text-white material-icons text-base" onClick={scrollToTop}>cottage</button>
          <h1 className="text-4xl font-bold text-center text-white font-bungee">
            🎬 DC Kino Showtimes
          </h1>
          <button className="text-white material-icons text-base" onClick={() => setShowCalendar(true)}>calendar_month</button>
        </div>
      </header>

      <header className="w-full bg-zinc-700 shadow-inner">
        <div className="w-full px-4 py-3 text-white text-center text-sm sm:text-base font-audiowide">
          <div className="flex flex-col sm:flex-row justify-center items-center space-y-2 sm:space-y-0 sm:gap-6">
            <button 
              className="bg-zinc-800 w-full sm:w-auto px-4 py-2 rounded flex items-center justify-center gap-2" 
              onClick={() => setShowMovieList(true)}
            >
              🎞️ {uniqueMovies.length} Movies Showing
            </button>
            <button 
              className="bg-zinc-800 w-full sm:w-auto px-4 py-2 rounded flex items-center justify-center gap-2" 
              onClick={() => setShowTheaterList(true)}
            >
              🏛️ {Object.keys(theaterMap).length} Theaters Listed
            </button>
            <button 
              className="bg-zinc-800 w-full sm:w-auto px-4 py-2 rounded flex items-center justify-center gap-2" 
              onClick={() => setShowOfflineList(true)}
            >
              🔌 {offlineTheaters.length > 0 ? `${offlineTheaters.length} Theater${offlineTheaters.length > 1 ? 's' : ''} Offline` : "All Theater Sites Online"}
            </button>
          </div>
        </div>
      </header>

      <main className="min-h-screen px-4 py-6 relative">
        <div className="w-full">
          <div className="flex flex-col gap-10">
            {Object.entries(groupedByDateAndTitle).map(([date, moviesByTitle]) => (
              <div key={date} id={`date-${new Date(date).toISOString().split("T")[0]}`} className="flex flex-col gap-4">
                <h2 className="text-4xl font-bold text-white border-b border-zinc-600 pb-2 font-montserratalts">
                  {date}
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                  {Object.entries(moviesByTitle).map(([title, showings], groupIdx) => {
                    const stackOffset = 32;
                    const stackHeight = 240 + (showings.length - 1) * stackOffset;
                    return (
                      <div key={title} className="relative" style={{ height: `${stackHeight}px` }}>
                        {[...showings]
                          .slice()
                          .sort((a, b) => getFirstTime(a).localeCompare(getFirstTime(b)))
                          .map((movie, idx, arr) => {
                            const theater = theaterMap[movie.theaterID];
                            const bgClass = theater?.colorClass || 'bg-zinc-800';
                            const normTitle = normalizeTitle(movie.title);
                            const posterUrl = posters[normTitle] || `/posters/${normTitle.replace(/\s+/g, '_')}.webp`;
                            return (
                              <div
                                key={movie.theaterID}
                                onClick={() => {
                                  setSelectedStack({ date, title: normTitle, idx });
                                }}
                                className="cursor-pointer absolute left-0 right-0 rounded-2xl shadow-lg flex flex-row overflow-hidden h-60 transition-transform duration-300 transform hover:scale-[1.03] hover:shadow-2xl"
                                style={{ top: `${idx * stackOffset}px`, zIndex: 10 + (arr.length - idx), opacity: 1 }}
                              >
                                <div className="absolute inset-0 bg-zinc-900" style={{ zIndex: 0 }} />
                                <div className="w-1/2 sm:w-1/3 h-full bg-zinc-700 flex items-center justify-center text-sm text-zinc-300 z-10">
                                  <img src={posterUrl} alt={movie.title} className="object-cover w-full h-full" onError={handleImageError} />
                                </div>
                                <div className={`absolute inset-0 ${bgClass}`} style={{ zIndex: 1 }} />
                                <div className="relative z-10 p-3 sm:p-6 flex flex-col justify-start w-1/2 sm:w-2/3 text-white">
                                  <div className="text-xl sm:text-2xl font-semibold mt-0 sm:mt-1 mb-2 sm:mb-4 font-limelight line-clamp-3">{movie.title}</div>
                                  <div className="mt-auto">
                                    <div className="text-zinc-100 text-xs sm:text-sm leading-tight mb-1 sm:mb-3 font-montserratalts">
                                      {movie.times.map(({ time, status }, i) => (
                                        <span key={i} className={status !== 'available' ? 'line-through' : ''}>
                                          {i > 0 ? ' • ' : ''}{time}
                                        </span>
                                      ))}
                                    </div>
                                    <div className="text-zinc-100 text-lg sm:text-xl font-alumnisc line-clamp-2">{theater?.name || 'Unknown Theater'}</div>
                                  </div>
                                </div>
                              </div>
                            );
                          })}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>

        {selectedStack && (
          <div className="fixed inset-0 z-50 bg-black bg-opacity-80 flex justify-center items-center p-4">
            <div className="text-white rounded-2xl shadow-xl p-6 w-full max-w-4xl relative flex flex-col md:flex-row gap-6 max-h-[95vh] overflow-y-auto">
              {(() => {
                const { date, title, idx } = selectedStack;
                const stack = groupedByDateAndTitle[date]?.[title]
                  ? [...groupedByDateAndTitle[date][title]].sort((a, b) => getFirstTime(a).localeCompare(getFirstTime(b)))
                  : null;

                if (stack) {
                  const currentMovie = stack[idx];
                  const bgClass = theaterMap[currentMovie.theaterID]?.colorClass || 'bg-zinc-800';
                  const normTitle = normalizeTitle(currentMovie.title);
                  const posterUrl = posters[normTitle] || `/posters/${normTitle.replace(/\s+/g, '_')}.webp`;
                  return (
                    <>
                      <div className="absolute inset-0 bg-zinc-900 rounded-2xl" style={{ zIndex: 0 }} />
                      <div className={`absolute inset-0 rounded-2xl ${bgClass}`} style={{ zIndex: 1 }} />
                      <button onClick={() => setSelectedStack(null)} className="absolute top-2 right-2 text-white text-2xl z-20">×</button>
                      <div className="w-full md:w-1/2 flex justify-center items-center z-10">
                        <img
                          src={posterUrl}
                          alt={currentMovie.title}
                          className="object-cover w-full max-h-[50vh] md:max-h-[80vh] rounded"
                          onError={handleImageError}
                        />
                      </div>
                      <div className="w-full md:w-1/2 flex flex-col justify-center z-10 relative pb-16 md:pb-0">
                        <h2 className="text-3xl font-bold mb-2 font-limelight">{currentMovie.title}</h2>
                        <p className="text-zinc-300 text-sm mb-2 font-montserratalts">{currentMovie.date}</p>
                        <p className="text-zinc-300 mb-2 text-sm font-montserratalts">
                          {currentMovie.times.map(({ time, status }, i) => (
                            <span key={i} className={status !== 'available' ? 'line-through' : ''}>
                              {i > 0 ? ' • ' : ''}{time}
                            </span>
                          ))}
                        </p>
                        <p className="text-zinc-100 text-xl font-alumnisc mb-4">{theaterMap[currentMovie.theaterID]?.name || 'Unknown Theater'}</p>
                        {stack.length > 1 && (
                          <div className="flex justify-center items-center gap-4 mt-4 absolute left-0 right-0 bottom-0 md:relative md:bottom-auto md:mt-4">
                            <button
                              className="bg-zinc-700 px-6 py-3 rounded-lg text-white font-bold text-2xl disabled:opacity-50 shadow-md hover:bg-zinc-600 transition-colors"
                              onClick={() => {
                                const prevIdx = (idx - 1 + stack.length) % stack.length;
                                setSelectedStack({ ...selectedStack, idx: prevIdx });
                              }}
                              disabled={stack.length < 2}
                            >
                              ◀
                            </button>
                            <span className="text-sm text-zinc-300">{idx + 1} / {stack.length}</span>
                            <button
                              className="bg-zinc-700 px-6 py-3 rounded-lg text-white font-bold text-2xl disabled:opacity-50 shadow-md hover:bg-zinc-600 transition-colors"
                              onClick={() => {
                                const nextIdx = (idx + 1) % stack.length;
                                setSelectedStack({ ...selectedStack, idx: nextIdx });
                              }}
                              disabled={stack.length < 2}
                            >
                              ▶
                            </button>
                          </div>
                        )}
                      </div>
                    </>
                  );
                }
                return null;
              })()}
            </div>
          </div>
        )}

        {showTheaterList && (
          <Modal title="Theaters Listed" onClose={() => setShowTheaterList(false)}>
            <ul className="list-disc pl-6 space-y-2 text-sm font-audiowide">
              {Object.values(theaterMap).map((theater, index) => (
                <li key={index}>{theater.name}</li>
              ))}
            </ul>
          </Modal>
        )}

        {showMovieList && (
          <Modal title="Movies Listed" onClose={() => setShowMovieList(false)}>
            <ul className="list-disc pl-6 space-y-2 text-sm font-audiowide">
              {uniqueMovies.map((title, index) => (
                <li key={index}>{title}</li>
              ))}
            </ul>
          </Modal>
        )}

        {showOfflineList && (
          <Modal title="Theater Status" onClose={() => setShowOfflineList(false)}>
            {offlineTheaters.length > 0 ? (
              <ul className="list-disc pl-6 space-y-2 text-sm font-audiowide">
                {offlineTheaters.map((theater, index) => (
                  <li key={index}>{theater.name}</li>
                ))}
              </ul>
            ) : (
              <p className="text-center text-sm font-audiowide">All theaters are currently online!</p>
            )}
          </Modal>
        )}

        {showCalendar && (
          <Modal title="Jump to Date" onClose={() => setShowCalendar(false)}>
            <div className="flex justify-center items-center w-full">
              <DatePicker
                selected={calendarDate}
                onChange={(date) => setCalendarDate(date)}
                inline
                includeDates={availableDates.map(d => new Date(d))}
                openToDate={calendarDate || (availableDates.length > 0 ? new Date(availableDates[0]) : new Date())}
              />
            </div>
          </Modal>
        )}
      </main>
    </>
  );
}