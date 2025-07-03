import React, { useEffect, useState } from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import "./index.css";
import movies from './data/movies.json';
import theaters from './data/theaters.json';
import { getPosterUrl } from './utils/tmdb';

// Normalize date to 'Mon D' (e.g., 'Jul 3')
function normalizeDate(dateStr) {
  // Match e.g. 'Jul 03' or 'Jul 3' and convert to 'Jul 3'
  const match = dateStr.match(/^(\w{3})\s0?(\d{1,2})$/);
  if (match) {
    return `${match[1]} ${parseInt(match[2], 10)}`;
  }
  return dateStr;
}

// Group and condense movies by normalized date and lowercase title (for stacking by movie, case-insensitive)
const groupedByDateAndTitle = movies.reduce((acc, movie) => {
  const lowerTitle = movie.title.toLowerCase();
  const normDate = normalizeDate(movie.date);
  if (!acc[normDate]) acc[normDate] = {};
  if (!acc[normDate][lowerTitle]) acc[normDate][lowerTitle] = [];
  // Find if this theater already exists for this movie on this date
  let theaterEntry = acc[normDate][lowerTitle].find(m => m.theaterID === movie.theaterID);
  if (!theaterEntry) {
    acc[normDate][lowerTitle].push({
      ...movie,
      date: normDate, // ensure all movies in group have normalized date
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
  const [selectedMovie, setSelectedMovie] = useState(null);
  const [showTheaterList, setShowTheaterList] = useState(false);
  const [showMovieList, setShowMovieList] = useState(false);
  const [showOfflineList, setShowOfflineList] = useState(false);
  const [showCalendar, setShowCalendar] = useState(false);
  const [calendarDate, setCalendarDate] = useState(null);

  useEffect(() => {
    const loadPosters = async () => {
      const results = {};
      const seen = new Set();
      for (const movie of movies) {
        const key = `${movie.title}|${movie.theaterID}`;
        if (!seen.has(key)) {
          seen.add(key);
          const url = await getPosterUrl(movie.title);
          if (url) results[movie.title] = url;
        }
      }
      setPosters(results);
    };
    loadPosters();
  }, []);

  const uniqueMovieKeys = new Set(movies.map(m => `${m.title}|${m.theaterID}`));
  const uniqueMovies = Array.from(new Set(movies.map(m => m.title)));
  const offlineTheaters = theaters.filter(theater => theater.online === false);
  const availableDates = Object.keys(groupedByDateAndTitle).sort((a, b) => {
    // Try to sort by month and day
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
      const yOffset = -120;
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
        <div className="w-full px-4 py-4 flex justify-between items-center">
          <button className="text-white material-icons text-base" onClick={scrollToTop}>cottage</button>
          <h1 className="text-4xl font-bold text-center text-white font-bungee">
            🎬 DC Kino Showtimes
          </h1>
          <button className="text-white material-icons text-base" onClick={() => setShowCalendar(true)}>calendar_month</button>
        </div>
      </header>

      <header className="w-full bg-zinc-700 shadow-inner">
        <div className="w-full px-4 py-3 text-white text-center text-sm sm:text-base font-audiowide">
          <div className="flex flex-col sm:flex-row justify-center items-center gap-2 sm:gap-6">
            <button className="bg-zinc-800" onClick={() => setShowMovieList(true)}>
              🎞️ {uniqueMovieKeys.size} Movies Showing
            </button>
            <button className="bg-zinc-800" onClick={() => setShowTheaterList(true)}>
              🏛️ {Object.keys(theaterMap).length} Theaters Listed
            </button>
            <button className="bg-zinc-800" onClick={() => setShowOfflineList(true)}>
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
                    // Overlay cards with vertical offset: top card is last in array
                    const stackOffset = 32; // px
                    const stackHeight = 240 + (showings.length - 1) * stackOffset;
                    return (
                      <div key={title} className="relative" style={{ height: `${stackHeight}px` }}>
                        {[...showings]
                          .slice()
                          .sort((a, b) => {
                            // Sort by earliest showing time (first time in times array)
                            const getFirstTime = (movie) => {
                              if (!movie.times || movie.times.length === 0) return '23:59';
                              // Assume time is in HH:MM or H:MM format
                              return movie.times[0].time;
                            };
                            return getFirstTime(a).localeCompare(getFirstTime(b));
                          })
                          .map((movie, idx, arr) => {
                            const theater = theaterMap[movie.theaterID];
                            const bgClass = theater?.colorClass || 'bg-zinc-800';
                            const posterUrl = posters[movie.title];
                            // Overlay: top card is at the top, each card below is lower
                            // idx=0 is top, idx=arr.length-1 is bottom
                            return (
                              <div
                                key={movie.theaterID}
                                onClick={() => setSelectedMovie({ ...movie, bgClass, date })}
                                className="cursor-pointer absolute left-0 right-0 rounded-2xl shadow-lg flex flex-col sm:flex-row overflow-hidden h-60 transition-transform duration-300 transform hover:scale-[1.03] hover:shadow-2xl"
                                style={{ top: `${idx * stackOffset}px`, zIndex: 10 + (arr.length - idx), opacity: 1 }}
                              >
                                {/* Blank card for background, same as site bg */}
                                <div className="absolute inset-0 bg-zinc-900" style={{ zIndex: 0 }} />
                                <div className="w-full sm:w-1/2 h-1/2 sm:h-full bg-zinc-700 flex items-center justify-center text-sm text-zinc-300 z-10">
                                  {posterUrl ? (
                                    <img src={posterUrl} alt={movie.title} className="object-cover w-full h-full" />
                                  ) : (
                                    movie.poster || 'Poster'
                                  )}
                                </div>
                                <div className={`absolute inset-0 ${bgClass}`} style={{ zIndex: 1 }} />
                                <div className="relative z-10 p-6 flex flex-col justify-start w-full text-white">
                                  <div className="text-2xl font-semibold mt-1 mb-4 font-limelight line-clamp-3">{movie.title}</div>
                                  <div className="mt-auto">
                                    <div className="text-zinc-100 text-sm leading-tight mb-3 font-montserratalts">
                                      {movie.times.map(({ time, status }, i) => (
                                        <span key={i} className={status !== 'available' ? 'line-through' : ''}>
                                          {i > 0 ? ' • ' : ''}{time}
                                        </span>
                                      ))}
                                    </div>
                                    <div className="text-zinc-100 text-xl font-alumnisc line-clamp-2">{theater?.name || 'Unknown Theater'}</div>
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

        {selectedMovie && (
          <div className="fixed inset-0 z-50 bg-black bg-opacity-80 flex justify-center items-center">
            <div className={`text-white rounded-2xl shadow-xl p-6 max-w-4xl w-full relative flex flex-col sm:flex-row gap-6`}>
              {/* Blank card for background, same as site bg, behind the colored card */}
              <div className="absolute inset-0 bg-zinc-900 rounded-2xl" style={{ zIndex: 0 }} />
              <div className={`absolute inset-0 rounded-2xl ${selectedMovie.bgClass}`} style={{ zIndex: 1 }} />
              <button onClick={() => setSelectedMovie(null)} className="absolute top-2 right-2 text-white text-2xl z-20">×</button>
              <div className="sm:w-1/2 flex justify-center items-center z-10">
                {posters[selectedMovie.title] ? (
                  <img src={posters[selectedMovie.title]} alt={selectedMovie.title} className="object-cover max-h-[500px] w-full rounded" />
                ) : (
                  <div className="bg-zinc-700 h-60 w-full flex items-center justify-center text-sm text-zinc-300">
                    {selectedMovie.poster || 'Poster Unavailable'}
                  </div>
                )}
              </div>
              <div className="sm:w-1/2 flex flex-col justify-center z-10">
                <h2 className="text-3xl font-bold mb-2 font-limelight">{selectedMovie.title}</h2>
                <p className="text-zinc-300 text-sm mb-2 font-montserratalts">{selectedMovie.date}</p>
                <p className="text-zinc-300 mb-2 text-sm font-montserratalts">
                  {selectedMovie.times.map(({ time, status }, i) => (
                    <span key={i} className={status !== 'available' ? 'line-through' : ''}>
                      {i > 0 ? ' • ' : ''}{time}
                    </span>
                  ))}
                </p>
                <p className="text-zinc-100 text-xl font-alumnisc mb-4">{theaterMap[selectedMovie.theaterID]?.name || 'Unknown Theater'}</p>
              </div>
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
            <DatePicker
              selected={calendarDate}
              onChange={(date) => setCalendarDate(date)}
              inline
              includeDates={availableDates.map(d => new Date(d))}
            />
          </Modal>
        )}
      </main>
    </>
  );
}
