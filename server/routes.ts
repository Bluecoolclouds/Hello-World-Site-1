import type { Express } from "express";
import type { Server } from "http";
import { storage } from "./storage";
import { api } from "@shared/routes";
import path from "path";
import Database from "better-sqlite3";

const photoCache = new Map<string, { buffer: Buffer; contentType: string; timestamp: number }>();
const PHOTO_CACHE_TTL = 3600000;

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {
  app.get(api.greeting.get.path, async (req, res) => {
    const greeting = await storage.getGreeting();
    res.json(greeting || { message: "Привет, Мир" });
  });

  app.get("/api/bot-stats", async (req, res) => {
    try {
      const fs = await import("fs");
      const candidates = [
        path.resolve(process.cwd(), "bot.db"),
        path.resolve(process.cwd(), "bot/dating_bot.db"),
      ];
      const dbPath = candidates.find((p) => fs.existsSync(p));
      if (!dbPath) {
        return res.json({ totalUsers: 0, totalGirls: 0, totalMen: 0, activeChats: 0, onlineNow: 0 });
      }
      const db = new Database(dbPath, { readonly: true });

      const totalUsers = db.prepare("SELECT COUNT(*) as count FROM users").get() as any;
      const totalGirls = db.prepare("SELECT COUNT(*) as count FROM users WHERE is_girl = 1").get() as any;
      const totalMen = db.prepare("SELECT COUNT(*) as count FROM users WHERE is_girl = 0 OR is_girl IS NULL").get() as any;

      let activeChats = { count: 0 };
      try {
        activeChats = db.prepare("SELECT COUNT(*) as count FROM bot_chats WHERE is_active = 1").get() as any;
      } catch {}

      db.close();

      const girlsCount = (totalGirls?.count || 0) + 10;
      const maxOnline = Math.floor(girlsCount / 2);
      const onlineRandom = Math.max(3, Math.floor(Math.random() * maxOnline) + 1);

      res.json({
        totalUsers: totalUsers?.count || 0,
        totalGirls: totalGirls?.count || 0,
        totalMen: totalMen?.count || 0,
        activeChats: activeChats?.count || 0,
        onlineNow: onlineRandom,
      });
    } catch {
      res.json({
        totalUsers: 0,
        totalGirls: 0,
        totalMen: 0,
        activeChats: 0,
        onlineNow: 0,
      });
    }
  });

  app.get("/api/top-girls", async (req, res) => {
    try {
      const fs = await import("fs");
      const candidates = [
        path.resolve(process.cwd(), "bot.db"),
        path.resolve(process.cwd(), "bot/dating_bot.db"),
      ];
      const dbPath = candidates.find((p) => fs.existsSync(p));
      if (!dbPath) {
        return res.json([]);
      }
      const db = new Database(dbPath, { readonly: true });

      let onlineGirls: any[] = [];
      let offlineGirls: any[] = [];
      try {
        onlineGirls = db.prepare(`
          SELECT user_id, name, age, city, photo_id, media_type, is_online, bio, breast, height, weight
          FROM users
          WHERE is_girl = 1 AND is_banned = 0 AND photo_id IS NOT NULL AND (media_type = 'photo' OR media_type IS NULL) AND is_online = 1
          ORDER BY view_count DESC
          LIMIT 3
        `).all();
        offlineGirls = db.prepare(`
          SELECT user_id, name, age, city, photo_id, media_type, is_online, bio, breast, height, weight
          FROM users
          WHERE is_girl = 1 AND is_banned = 0 AND photo_id IS NOT NULL AND (media_type = 'photo' OR media_type IS NULL) AND (is_online = 0 OR is_online IS NULL)
          ORDER BY view_count DESC
          LIMIT 3
        `).all();
      } catch {}

      db.close();

      function shuffle(arr: any[]) {
        for (let i = arr.length - 1; i > 0; i--) {
          const j = Math.floor(Math.random() * (i + 1));
          [arr[i], arr[j]] = [arr[j], arr[i]];
        }
      }
      shuffle(onlineGirls);
      shuffle(offlineGirls);
      const top3 = [...onlineGirls, ...offlineGirls].slice(0, 3);

      res.json(top3.map((g: any) => ({
        id: g.user_id,
        name: g.name || "Без имени",
        age: g.age,
        city: g.city,
        bio: g.bio ? g.bio.substring(0, 100) : "",
        isOnline: g.is_online === 1,
        height: g.height,
        weight: g.weight,
        breast: g.breast,
        hasPhoto: !!g.photo_id,
      })));
    } catch {
      res.json([]);
    }
  });

  app.get("/api/girl-photo/:userId", async (req, res) => {
    try {
      const botToken = process.env.BOT_TOKEN;
      if (!botToken) {
        return res.status(404).send("No token");
      }

      const fs = await import("fs");
      const candidates = [
        path.resolve(process.cwd(), "bot.db"),
        path.resolve(process.cwd(), "bot/dating_bot.db"),
      ];
      const dbPath = candidates.find((p) => fs.existsSync(p));
      if (!dbPath) {
        return res.status(404).send("Not found");
      }
      const db = new Database(dbPath, { readonly: true });

      const girl = db.prepare(
        "SELECT photo_id FROM users WHERE user_id = ? AND is_girl = 1"
      ).get(req.params.userId) as any;
      db.close();

      if (!girl?.photo_id) {
        return res.status(404).send("Not found");
      }

      const cacheKey = req.params.userId;
      const cached = photoCache.get(cacheKey);
      if (cached && Date.now() - cached.timestamp < PHOTO_CACHE_TTL) {
        res.set("Content-Type", cached.contentType);
        res.set("Cache-Control", "public, max-age=3600");
        return res.send(cached.buffer);
      }

      const fileResp = await fetch(
        `https://api.telegram.org/bot${botToken}/getFile?file_id=${girl.photo_id}`
      );
      const fileData = await fileResp.json() as any;

      if (!fileData.ok || !fileData.result?.file_path) {
        return res.status(404).send("Not found");
      }

      const photoUrl = `https://api.telegram.org/file/bot${botToken}/${fileData.result.file_path}`;
      const photoResp = await fetch(photoUrl);

      if (!photoResp.ok) {
        return res.status(404).send("Not found");
      }

      const contentType = photoResp.headers.get("content-type") || "image/jpeg";
      const buffer = Buffer.from(await photoResp.arrayBuffer());

      photoCache.set(cacheKey, { buffer, contentType, timestamp: Date.now() });

      res.set("Content-Type", contentType);
      res.set("Cache-Control", "public, max-age=3600");
      res.send(buffer);
    } catch {
      res.status(500).send("Error");
    }
  });

  return httpServer;
}
