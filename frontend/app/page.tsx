"use client";

import { useMemo, useState } from "react";

type Position = "QB" | "RB" | "WR" | "TE";

type Player = {
  id: number;
  name: string;
  position: Position;
  team: string;
  ppr: number;
  primaryMetric: string;
  primaryLabel: string;
  snapShare: string;
  trend: number[];
};

const players: Player[] = [
  {
    id: 1,
    name: "Amon-Ra St. Brown",
    position: "WR",
    team: "DET",
    ppr: 28.7,
    primaryMetric: "9.0",
    primaryLabel: "Targets",
    snapShare: "92%",
    trend: [17, 21, 24, 20, 28],
  },
  {
    id: 2,
    name: "Patrick Mahomes",
    position: "QB",
    team: "KC",
    ppr: 21.7,
    primaryMetric: "286",
    primaryLabel: "Pass yds",
    snapShare: "100%",
    trend: [18, 22, 19, 24, 21],
  },
  {
    id: 3,
    name: "Josh Jacobs",
    position: "RB",
    team: "GB",
    ppr: 17.3,
    primaryMetric: "19.0",
    primaryLabel: "Opportunities",
    snapShare: "71%",
    trend: [13, 15, 17, 16, 18],
  },
  {
    id: 4,
    name: "A.J. Brown",
    position: "WR",
    team: "NE",
    ppr: 16.8,
    primaryMetric: "8.0",
    primaryLabel: "Targets",
    snapShare: "84%",
    trend: [11, 14, 13, 16, 17],
  },
  {
    id: 5,
    name: "Harold Fannin",
    position: "TE",
    team: "CLE",
    ppr: 11.2,
    primaryMetric: "6.0",
    primaryLabel: "Targets",
    snapShare: "76%",
    trend: [6, 8, 9, 10, 11],
  },
];

const insights = [
  {
    title: "WR room is your biggest edge",
    body: "Your receivers account for the strongest share of weekly roster production.",
    type: "positive",
    badge: "High confidence",
  },
  {
    title: "RB depth deserves attention",
    body: "Your starters are stable, but the bench lacks a clear injury-away breakout option.",
    type: "warning",
    badge: "Medium",
  },
  {
    title: "Target volume is trending upward",
    body: "Several available receivers are earning enough usage to deserve waiver consideration.",
    type: "info",
    badge: "Data-backed",
  },
  {
    title: "Trade WR surplus for RB stability",
    body: "Your roster construction supports dealing from receiver depth instead of adding another WR.",
    type: "trade",
    badge: "Strategic",
  },
];

function Sparkline({ values }: { values: number[] }) {
  const max = Math.max(...values);
  const min = Math.min(...values);

  const points = values
    .map((value, index) => {
      const x = (index / (values.length - 1)) * 100;
      const y =
        42 -
        ((value - min) / Math.max(max - min, 1)) * 30;

      return `${x},${y}`;
    })
    .join(" ");

  return (
    <svg
      viewBox="0 0 100 48"
      preserveAspectRatio="none"
      className="sparkline"
    >
      <polyline
        points={points}
        fill="none"
        stroke="currentColor"
        strokeWidth="2.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function LockerRoom() {
  const [position, setPosition] =
    useState<"ALL" | Position>("ALL");

  const [index, setIndex] = useState(0);

  const filteredPlayers = useMemo(() => {
    if (position === "ALL") {
      return players;
    }

    return players.filter(
      (player) => player.position === position
    );
  }, [position]);

  const player =
    filteredPlayers[
      index % Math.max(filteredPlayers.length, 1)
    ];

  function selectPosition(next: "ALL" | Position) {
    setPosition(next);
    setIndex(0);
  }

  function nextPlayer() {
    setIndex((current) =>
      (current + 1) % filteredPlayers.length
    );
  }

  function previousPlayer() {
    setIndex((current) =>
      (current - 1 + filteredPlayers.length) %
      filteredPlayers.length
    );
  }

  return (
    <section className="panel locker-room">
      <header className="panel-header">
        <div>
          <div className="eyebrow">ROSTER EXPLORER</div>
          <h2>Locker Room</h2>
          <p>Scroll your roster and inspect usage.</p>
        </div>

        <span className="counter">
          {filteredPlayers.length
            ? (index % filteredPlayers.length) + 1
            : 0}
          {" / "}
          {filteredPlayers.length}
        </span>
      </header>

      <div className="position-tabs">
        {(["ALL", "QB", "RB", "WR", "TE"] as const).map(
          (item) => (
            <button
              key={item}
              className={
                position === item ? "active" : ""
              }
              onClick={() => selectPosition(item)}
            >
              {item === "ALL" ? "All" : item}
            </button>
          )
        )}
      </div>

      {player && (
        <div className="locker-carousel">
          <button
            className="carousel-button"
            onClick={previousPlayer}
            aria-label="Previous player"
          >
            ‹
          </button>

          <article className="player-card">
            <div className="player-art">
              <span className="player-badge">
                {player.position} · {player.team}
              </span>

              <div className="head-placeholder" />
              <div className="body-placeholder" />
            </div>

            <div className="player-content">
              <div>
                <h3>{player.name}</h3>
                <p>
                  {player.position} · {player.team} ·
                  2026 season
                </p>
              </div>

              <div className="metric-grid">
                <div className="metric-card">
                  <strong>{player.ppr}</strong>
                  <span>PPR points</span>
                </div>

                <div className="metric-card">
                  <strong>
                    {player.primaryMetric}
                  </strong>
                  <span>{player.primaryLabel}</span>
                </div>

                <div className="metric-card">
                  <strong>{player.snapShare}</strong>
                  <span>Snap share</span>
                </div>

                <div className="metric-card trend-up">
                  <strong>↑</strong>
                  <span>Usage direction</span>
                </div>
              </div>

              <div className="trend-card">
                <div className="trend-heading">
                  <span>Recent fantasy trend</span>
                  <span>Last 5</span>
                </div>

                <Sparkline values={player.trend} />
              </div>
            </div>
          </article>

          <button
            className="carousel-button"
            onClick={nextPlayer}
            aria-label="Next player"
          >
            ›
          </button>
        </div>
      )}

      <div className="carousel-dots">
        {filteredPlayers.map((playerItem, dotIndex) => (
          <button
            key={playerItem.id}
            aria-label={`View ${playerItem.name}`}
            onClick={() => setIndex(dotIndex)}
            className={
              dotIndex ===
              index % filteredPlayers.length
                ? "active"
                : ""
            }
          />
        ))}
      </div>
    </section>
  );
}

function ResearchAgent() {
  type Message = {
    role: "user" | "assistant";
    text: string;
  };

  const [messages, setMessages] =
    useState<Message[]>([
      {
        role: "user",
        text:
          "Which unrostered WRs have the strongest target volume?",
      },
      {
        role: "assistant",
        text:
          "Click Target upside below to retrieve live data from the Azure analytics backend.",
      },
    ]);

  const [input, setInput] = useState("");

  const [loading, setLoading] =
    useState(false);

  async function getTargetUpside() {
    if (loading) {
      return;
    }

    setMessages((current) => [
      ...current,
      {
        role: "user",
        text:
          "Which unrostered WRs have the strongest target volume?",
      },
    ]);

    setLoading(true);

    try {
      const response = await fetch(
        "/api/player-search",
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify({
            position: "WR",

            availability:
              "unrostered",

            sort_by: [
              "avg_targets",
            ],

            filters: [],

            last_n_weeks: null,

            limit: 5,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ??
            data.error ??
            "Player search failed."
        );
      }

      const rows = data.rows ?? [];

      if (!rows.length) {
        setMessages((current) => [
          ...current,
          {
            role: "assistant",
            text:
              "No qualifying unrostered wide receivers were returned.",
          },
        ]);

        return;
      }

      const resultText = rows
        .map(
          (
            player: {
              name: string;
              team: string;
              avg_targets: number;
              avg_snap_pct: number | null;
              avg_ppr: number | null;
            },
            index: number
          ) => {
            const snap =
              player.avg_snap_pct ??
              "N/A";

            const ppr =
              player.avg_ppr ??
              "N/A";

            return (
              `${index + 1}. ` +
              `${player.name} (${player.team})` +
              ` — ${player.avg_targets} targets, ` +
              `${snap}% snaps, ` +
              `${ppr} PPR`
            );
          }
        )
        .join("\n");

      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          text:
            "Top available WRs by target volume:\n\n" +
            resultText,
        },
      ]);
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Unknown error";

      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          text:
            `Live analytics request failed: ${message}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function sendMockMessage() {
    const trimmed =
      input.trim();

    if (!trimmed) {
      return;
    }

    setMessages((current) => [
      ...current,
      {
        role: "user",
        text: trimmed,
      },
      {
        role: "assistant",
        text:
          "Freeform chat is still mocked in this baseline. The Target upside action is already connected to the real Azure analytics backend.",
      },
    ]);

    setInput("");
  }

  return (
    <section className="panel research-agent">
      <header className="panel-header">
        <div>
          <div className="eyebrow">
            AI RESEARCH
          </div>

          <h2>
            Research Agent
          </h2>

          <p>
            Grounded in your league data.
          </p>
        </div>

        <button className="ghost-button">
          History
        </button>
      </header>

      <div className="agent-hero">
        <div className="agent-orb">
          <i />
          <i />
          <span />
        </div>

        <h3>
          Ask. Research. Decide.
        </h3>

        <p>
          Evidence-backed fantasy analysis
          using your roster, league context,
          and NFL usage data.
        </p>
      </div>

      <div className="quick-prompts">
        <button>
          Best waiver pickups
        </button>

        <button>
          Trade check
        </button>

        <button>
          Start / Sit
        </button>

        <button
          onClick={getTargetUpside}
          disabled={loading}
        >
          {loading
            ? "Researching..."
            : "Target upside"}
        </button>
      </div>

      <div className="message-list">
        {messages.map(
          (
            message,
            messageIndex
          ) => (
            <div
              key={messageIndex}
              className={
                `message ${message.role}`
              }
            >
              <div
                style={{
                  whiteSpace:
                    "pre-line",
                }}
              >
                {message.text}
              </div>

              {message.role ===
                "assistant" && (
                <div className="evidence-tag">
                  Sleeper · nflverse · Azure
                </div>
              )}
            </div>
          )
        )}
      </div>

      <div className="chat-input">
        <input
          value={input}
          onChange={(event) =>
            setInput(
              event.target.value
            )
          }
          onKeyDown={(event) => {
            if (
              event.key ===
              "Enter"
            ) {
              sendMockMessage();
            }
          }}
          placeholder="Ask about players, trades, waivers, or lineups..."
        />

        <button
          onClick={sendMockMessage}
        >
          ↑
        </button>
      </div>
    </section>
  );
}

export default function Home() {
  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">↔</div>
          <span>FourthDown AI</span>
        </div>

        <nav>
          <button className="active">Dashboard</button>
          <button>Team</button>
          <button>Research</button>
          <button>Insights</button>
        </nav>

        <div className="top-actions">
          <span className="week-pill">
            Week 5 · 2026
          </span>
          <div className="avatar">NJ</div>
        </div>
      </header>

      <div className="dashboard-grid">
        <section className="panel your-team">
          <header className="panel-header">
            <div>
              <div className="eyebrow">
                LEAGUE OVERVIEW
              </div>
              <h2>Your Team</h2>
              <p>Outside huzz · PPR</p>
            </div>
          </header>

          <div className="team-stats">
            <div className="team-stat standing">
              <strong>1st</strong>
              <span>League standing</span>
            </div>

            <div className="team-stat">
              <strong>4–0</strong>
              <span>Record</span>
            </div>
          </div>

          <div className="matchup-card">
            <div className="matchup-title">
              <strong>This Week Matchup</strong>
              <span>Week 5</span>
            </div>

            <div className="matchup-teams">
              <div>
                <strong>118.6</strong>
                <span>Your team</span>
              </div>

              <i>VS</i>

              <div>
                <strong>111.2</strong>
                <span>Opponent</span>
              </div>
            </div>

            <div className="probability-bar">
              <span />
            </div>

            <div className="probability-labels">
              <span>62% win chance</span>
              <span>38%</span>
            </div>
          </div>
        </section>

        <LockerRoom />

        <ResearchAgent />

        <section className="panel analytics">
          <header className="panel-header">
            <div>
              <div className="eyebrow">
                TEAM PERFORMANCE
              </div>
              <h2>Analytics</h2>
              <p>
                Roster production and scoring trends.
              </p>
            </div>

            <button className="ghost-button">
              This season
            </button>
          </header>

          <div className="analytics-row">
            <div className="analytics-card">
              <h3>Points by position</h3>

              <div className="donut-layout">
                <div className="donut">
                  <div />
                </div>

                <div className="legend">
                  <span>
                    WR <strong>32%</strong>
                  </span>
                  <span>
                    RB <strong>26%</strong>
                  </span>
                  <span>
                    QB <strong>19%</strong>
                  </span>
                  <span>
                    TE <strong>13%</strong>
                  </span>
                </div>
              </div>
            </div>

            <div className="analytics-card">
              <h3>Opportunity mix</h3>

              <div className="stat-list">
                <span>
                  Targets <strong>42</strong>
                </span>
                <span>
                  Carries <strong>37</strong>
                </span>
                <span>
                  Avg snap share <strong>68%</strong>
                </span>
              </div>
            </div>
          </div>

          <div className="analytics-card score-chart">
            <h3>Weekly score trend</h3>

            <svg
              viewBox="0 0 500 120"
              preserveAspectRatio="none"
            >
              <path
                d="M0 89 L125 73 L250 79 L375 48 L500 31"
                className="score-line"
              />

              <path
                d="M0 96 L125 88 L250 82 L375 77 L500 72"
                className="league-line"
              />
            </svg>

            <div className="weeks">
              <span>W1</span>
              <span>W2</span>
              <span>W3</span>
              <span>W4</span>
              <span>W5</span>
            </div>
          </div>
        </section>

        <section className="panel insights">
          <header className="panel-header">
            <div>
              <div className="eyebrow">
                EVIDENCE ENGINE
              </div>
              <h2>Insights</h2>
              <p>
                AI-generated findings backed by data.
              </p>
            </div>
          </header>

          <div className="insight-list">
            {insights.map((insight) => (
              <article
                key={insight.title}
                className={`insight ${insight.type}`}
              >
                <div>
                  <h3>{insight.title}</h3>
                  <p>{insight.body}</p>
                </div>

                <span>{insight.badge}</span>
              </article>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}