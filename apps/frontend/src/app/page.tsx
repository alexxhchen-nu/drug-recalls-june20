"use client";

import {
  ArrowRight,
  BookOpen,
  ClipboardList,
  Database,
  FileSearch,
  HeartPulse,
  Search,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

const examples = [
  "cats with serious adverse events after Bexagliflozin",
  "dog vomiting adverse event",
  "death reported serious adverse event dog",
  "lack of expected effectiveness in cats",
];

const sampleResults = [
  {
    report: "N141285",
    product: "Bexagliflozin",
    species: "Cat",
    breed: "Domestic Shorthair",
    status: "Ongoing",
    serious: true,
    score: "0.6626",
  },
  {
    report: "N141566",
    product: "Bexagliflozin",
    species: "Cat",
    breed: "Domestic Shorthair",
    status: "Outcome Unknown",
    serious: false,
    score: "0.6789",
  },
];

function Badge({
  children,
  tone = "cream",
}: {
  children: React.ReactNode;
  tone?: "cream" | "blue" | "red" | "green" | "yellow";
}) {
  const tones = {
    cream: "bg-[#fff8e7] text-zinc-950",
    blue: "bg-[#1f5aa6] text-white",
    red: "bg-[#d83a31] text-white",
    green: "bg-[#3f7d58] text-white",
    yellow: "bg-[#f3c84b] text-zinc-950",
  };

  return (
    <span
      className={`inline-flex items-center rounded-full border-2 border-zinc-950 px-3 py-1 text-xs font-black uppercase tracking-wide ${tones[tone]}`}
    >
      {children}
    </span>
  );
}

function Panel({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`comic-shadow relative overflow-hidden border-[3px] border-zinc-950 bg-[#fff8e7] ${className}`}
    >
      {children}
    </div>
  );
}

function Caption({
  children,
  color = "yellow",
}: {
  children: React.ReactNode;
  color?: "yellow" | "blue" | "red";
}) {
  const colors = {
    yellow: "bg-[#f3c84b]",
    blue: "bg-[#1f5aa6] text-white",
    red: "bg-[#d83a31] text-white",
  };

  return (
    <div
      className={`inline-block rotate-[-1.5deg] border-[3px] border-zinc-950 px-4 py-2 text-sm font-black uppercase tracking-wide comic-shadow-sm ${colors[color]}`}
    >
      {children}
    </div>
  );
}

export default function Home() {
  return (
    <main className="min-h-screen overflow-hidden">
      <div className="fixed inset-0 pointer-events-none opacity-30 halftone" />

      <header className="relative mx-auto flex max-w-7xl items-center justify-between px-6 py-7">
        <div className="flex items-center gap-3">
          <div className="grid h-12 w-12 place-items-center rounded-full border-[3px] border-zinc-950 bg-[#f3c84b] comic-shadow-sm">
            <FileSearch className="h-6 w-6" />
          </div>
          <div>
            <div className="text-xl font-black tracking-tight">
              FDA Animal Safety Search
            </div>
            <div className="hand text-lg leading-none text-zinc-700">
              field notes from public safety records
            </div>
          </div>
        </div>

        <nav className="hidden items-center gap-2 md:flex">
          <a
            href="#how"
            className="rounded-full border-2 border-zinc-950 bg-[#fff8e7] px-4 py-2 text-sm font-black comic-shadow-sm transition hover:translate-x-1 hover:translate-y-1 hover:shadow-none"
          >
            How it works
          </a>
          <a
            href="#evidence"
            className="rounded-full border-2 border-zinc-950 bg-[#fff8e7] px-4 py-2 text-sm font-black comic-shadow-sm transition hover:translate-x-1 hover:translate-y-1 hover:shadow-none"
          >
            Evidence
          </a>
          <a
            href="#search"
            className="rounded-full border-2 border-zinc-950 bg-[#d83a31] px-5 py-2 text-sm font-black text-white comic-shadow-sm transition hover:translate-x-1 hover:translate-y-1 hover:shadow-none"
          >
            Open search
          </a>
        </nav>
      </header>

      <section className="relative mx-auto grid max-w-7xl gap-8 px-6 pb-16 pt-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
        <div>
          <Caption color="yellow">Case file no. 001</Caption>

          <h1 className="mt-7 max-w-4xl text-6xl font-black leading-[0.9] tracking-[-0.07em] text-zinc-950 md:text-8xl">
            Search FDA animal safety records like a case file.
          </h1>

          <p className="mt-7 max-w-2xl text-xl font-semibold leading-9 text-zinc-800">
            A comic-inspired interface for non-technical teams exploring FDA animal
            and veterinary safety reports. Ask about products, species, adverse
            events, seriousness, and outcomes.
          </p>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <a
              href="#search"
              className="inline-flex items-center justify-center gap-2 rounded-full border-[3px] border-zinc-950 bg-[#1f5aa6] px-7 py-4 text-sm font-black uppercase tracking-wide text-white comic-shadow transition hover:translate-x-2 hover:translate-y-2 hover:shadow-none"
            >
              Start investigating
              <ArrowRight className="h-4 w-4" />
            </a>

            <a
              href="#how"
              className="inline-flex items-center justify-center rounded-full border-[3px] border-zinc-950 bg-[#fff8e7] px-7 py-4 text-sm font-black uppercase tracking-wide comic-shadow transition hover:translate-x-2 hover:translate-y-2 hover:shadow-none"
            >
              See the method
            </a>
          </div>

          <div className="mt-8 flex flex-wrap gap-2">
            <Badge tone="blue">Qdrant</Badge>
            <Badge tone="yellow">FDA records</Badge>
            <Badge tone="cream">Evidence cards</Badge>
            <Badge tone="green">Plain-English</Badge>
          </div>
        </div>

        <Panel className="rotate-[1deg] rounded-[2rem] p-5">
          <div className="absolute right-[-4rem] top-[-4rem] h-40 w-40 rounded-full bg-[#f3c84b]" />
          <div className="absolute bottom-[-3rem] left-[-3rem] h-36 w-36 rounded-full bg-[#d83a31]" />

          <div className="relative rounded-[1.5rem] border-[3px] border-zinc-950 bg-[#1f5aa6] p-5 text-white">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <div className="hand text-2xl text-[#f3c84b]">
                  Investigator console
                </div>
                <div className="text-3xl font-black tracking-tight">
                  Animal Safety Search
                </div>
              </div>

              <div className="rounded-full border-2 border-white bg-white/10 px-3 py-1 text-xs font-black">
                fda2025q1
              </div>
            </div>

            <div className="rounded-3xl border-[3px] border-zinc-950 bg-[#fff8e7] p-4 text-zinc-950">
              <div className="mb-3 flex items-center gap-2 text-sm font-black uppercase tracking-wide">
                <Search className="h-4 w-4" />
                Search question
              </div>

              <div className="hand rounded-2xl border-[3px] border-zinc-950 bg-white p-4 text-2xl leading-8">
                cats with serious adverse events after Bexagliflozin
              </div>

              <button className="mt-4 w-full rounded-full border-[3px] border-zinc-950 bg-[#d83a31] px-5 py-3 text-sm font-black uppercase tracking-wide text-white comic-shadow-sm">
                Search records
              </button>
            </div>

            <div className="mt-4 rounded-3xl border-[3px] border-white/80 bg-white/10 p-4">
              <div className="mb-2 hand text-2xl text-[#f3c84b]">
                Summary note
              </div>
              <p className="text-sm font-semibold leading-6 text-white">
                Found relevant cat reports involving Bexagliflozin. Some reports
                are marked serious adverse events and include ongoing or unknown
                outcomes.
              </p>
            </div>
          </div>
        </Panel>
      </section>

      <section id="how" className="relative mx-auto max-w-7xl px-6 py-10">
        <div className="mb-8">
          <Caption color="blue">How it works</Caption>
          <h2 className="mt-6 text-4xl font-black tracking-[-0.04em] md:text-6xl">
            Less database. More detective board.
          </h2>
        </div>

        <div className="grid gap-5 md:grid-cols-4">
          {[
            {
              icon: Search,
              title: "Ask naturally",
              body: "Search with human questions, not database syntax.",
              color: "bg-[#f3c84b]",
            },
            {
              icon: Database,
              title: "Find records",
              body: "The backend searches your Qdrant FDA index.",
              color: "bg-[#1f5aa6] text-white",
            },
            {
              icon: ClipboardList,
              title: "Extract fields",
              body: "Reports become clear cards with species, products, and status.",
              color: "bg-[#d83a31] text-white",
            },
            {
              icon: ShieldCheck,
              title: "Show evidence",
              body: "Every answer keeps the original record available.",
              color: "bg-[#3f7d58] text-white",
            },
          ].map((item) => {
            const Icon = item.icon;

            return (
              <Panel key={item.title} className="rounded-[1.75rem] p-5">
                <div
                  className={`mb-5 grid h-14 w-14 place-items-center rounded-2xl border-[3px] border-zinc-950 ${item.color}`}
                >
                  <Icon className="h-6 w-6" />
                </div>
                <h3 className="text-2xl font-black tracking-tight">{item.title}</h3>
                <p className="mt-3 text-base font-semibold leading-7 text-zinc-700">
                  {item.body}
                </p>
              </Panel>
            );
          })}
        </div>
      </section>

      <section id="search" className="relative mx-auto max-w-7xl px-6 py-12">
        <Panel className="rounded-[2rem] p-6 md:p-8">
          <div className="grid gap-8 lg:grid-cols-[0.9fr_1.1fr]">
            <div>
              <Caption color="red">Search preview</Caption>

              <h2 className="mt-6 text-4xl font-black tracking-[-0.04em] md:text-6xl">
                The public-facing app goes here.
              </h2>

              <p className="mt-5 text-lg font-semibold leading-8 text-zinc-700">
                This is the website shell for Vercel. Next, we wire this search
                area to your VPS FastAPI backend and replace these samples with
                live FDA/Qdrant results.
              </p>

              <div className="mt-6 space-y-3">
                {examples.map((example) => (
                  <div
                    key={example}
                    className="hand rounded-2xl border-[3px] border-zinc-950 bg-white px-4 py-3 text-xl comic-shadow-sm"
                  >
                    “{example}”
                  </div>
                ))}
              </div>
            </div>

            <div id="evidence" className="space-y-4">
              {sampleResults.map((result) => (
                <div
                  key={result.report}
                  className="rounded-[1.75rem] border-[3px] border-zinc-950 bg-white p-5 comic-shadow-sm"
                >
                  <div className="mb-3 flex flex-wrap gap-2">
                    <Badge tone="cream">{result.report}</Badge>
                    <Badge tone="blue">{result.species}</Badge>
                    <Badge tone={result.serious ? "red" : "green"}>
                      {result.serious ? "Serious AE" : "Non-serious"}
                    </Badge>
                  </div>

                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h3 className="text-3xl font-black tracking-tight">
                        {result.product}
                      </h3>
                      <p className="mt-2 text-base font-semibold text-zinc-600">
                        {result.breed} · {result.status}
                      </p>
                    </div>

                    <div className="rounded-2xl border-[3px] border-zinc-950 bg-[#f3c84b] px-4 py-3 text-right">
                      <div className="text-xs font-black uppercase">Match</div>
                      <div className="text-2xl font-black">{result.score}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Panel>
      </section>

      <section className="relative mx-auto max-w-7xl px-6 py-12">
        <Panel className="rounded-[2rem] bg-[#fff8e7] p-8">
          <div className="grid gap-8 md:grid-cols-[0.8fr_1.2fr] md:items-center">
            <div>
              <BookOpen className="h-14 w-14" />
              <h2 className="mt-4 text-4xl font-black tracking-[-0.04em]">
                Built for readers, reviewers, and teams.
              </h2>
            </div>

            <p className="hand text-3xl leading-10 text-zinc-800">
              “The goal is not to make people learn the database. The goal is to
              make the evidence legible.”
            </p>
          </div>
        </Panel>
      </section>

      <footer className="relative mx-auto max-w-7xl px-6 py-10">
        <div className="flex flex-col justify-between gap-4 border-t-[3px] border-zinc-950 pt-8 text-sm font-black uppercase tracking-wide text-zinc-700 md:flex-row">
          <div>FDA Animal Safety Search</div>
          <div>Evidence search only. Not medical advice.</div>
        </div>
      </footer>
    </main>
  );
}
