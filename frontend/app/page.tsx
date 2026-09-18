"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  ShieldCheck,
  MessageSquare,
  Mic,
  Brain,
  Globe,
  Lock,
  ArrowRight,
  AlertTriangle,
  CreditCard,
  PhoneCall,
} from "lucide-react";

const features = [
  {
    icon: Globe,
    title: "Multilingual",
    description: "Ask in Hindi, English, or your regional language — text or voice.",
  },
  {
    icon: Brain,
    title: "Intent-Aware RAG",
    description:
      "Understands what you're really asking — not just keyword matches — against verified RBI/NPCI advisories.",
  },
  {
    icon: Lock,
    title: "Persistent Memory",
    description:
      "Remembers your prior queries and reported incidents to give personalized advice every session.",
  },
  {
    icon: AlertTriangle,
    title: "Scam Classification",
    description:
      "Classifies suspicious messages into scam types (UPI collect, phishing, voice-phishing, etc.) with a confidence score.",
  },
];

const scamTypes = [
  { icon: CreditCard, label: "UPI Collect Scams" },
  { icon: AlertTriangle, label: "Phishing Links" },
  { icon: PhoneCall, label: "Voice Phishing" },
  { icon: CreditCard, label: "Fake Refund Scams" },
  { icon: AlertTriangle, label: "OTP Fraud" },
  { icon: PhoneCall, label: "SIM Swap" },
];

export default function HomePage() {
  return (
    <div className="flex flex-col items-center">
      {/* Hero */}
      <section className="w-full max-w-5xl mx-auto px-6 pt-20 pb-16 text-center">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-brand-900/60 border border-brand-700/50 text-brand-300 text-sm font-medium mb-6">
            <ShieldCheck className="w-4 h-4" />
            Grounded in RBI &amp; NPCI Advisories
          </div>

          <h1 className="text-5xl sm:text-6xl font-bold text-slate-50 leading-tight mb-6">
            Is that message a{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-400 to-blue-400">
              scam?
            </span>
          </h1>

          <p className="text-lg text-slate-400 max-w-2xl mx-auto mb-10">
            FraudGuard AI helps you identify financial fraud and scam patterns — in your
            language, by voice or text — using India&apos;s official fraud advisories.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/chat" className="btn-primary text-base px-6 py-3">
              <MessageSquare className="w-5 h-5" />
              Chat with AI
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link href="/voice" className="btn-secondary text-base px-6 py-3">
              <Mic className="w-5 h-5" />
              Try Voice Mode
            </Link>
          </div>
        </motion.div>
      </section>

      {/* Scam types strip */}
      <section className="w-full bg-slate-800/40 border-y border-slate-700/50 py-6 overflow-hidden">
        <div className="flex gap-8 animate-marquee whitespace-nowrap px-8">
          {[...scamTypes, ...scamTypes].map((s, i) => (
            <div
              key={i}
              className="inline-flex items-center gap-2 text-slate-400 text-sm font-medium"
            >
              <s.icon className="w-4 h-4 text-brand-400 flex-shrink-0" />
              {s.label}
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="w-full max-w-5xl mx-auto px-6 py-20">
        <motion.h2
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="text-3xl font-bold text-slate-50 text-center mb-12"
        >
          How it protects you
        </motion.h2>

        <div className="grid sm:grid-cols-2 gap-6">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="glass-card p-6 flex gap-4"
            >
              <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-brand-900/60 flex items-center justify-center">
                <f.icon className="w-5 h-5 text-brand-400" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-100 mb-1">{f.title}</h3>
                <p className="text-slate-400 text-sm leading-relaxed">{f.description}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="w-full max-w-5xl mx-auto px-6 pb-20 text-center">
        <div className="glass-card p-10">
          <h2 className="text-2xl font-bold text-slate-50 mb-3">
            Received a suspicious message?
          </h2>
          <p className="text-slate-400 mb-6">
            Paste it in the chat or describe it by voice. Get an instant, grounded verdict.
          </p>
          <Link href="/chat" className="btn-primary text-base px-8 py-3">
            Analyse Now <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>
    </div>
  );
}
