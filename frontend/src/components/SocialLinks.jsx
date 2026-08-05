import { FaGithub, FaLinkedin, FaMedium, FaTwitter } from "react-icons/fa";
import { FiGlobe } from "react-icons/fi";

import { SOCIAL_PLATFORM_LABELS } from "../utils/constants";

const PLATFORM_ICONS = {
  LINKEDIN: FaLinkedin,
  GITHUB: FaGithub,
  TWITTER: FaTwitter,
  MEDIUM: FaMedium,
  PORTFOLIO: FiGlobe,
};

function withProtocol(url) {
  return /^https?:\/\//i.test(url) ? url : `https://${url}`;
}

export default function SocialLinks({ profiles }) {
  if (!profiles || profiles.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2">
      {profiles.map((profile) => {
        const Icon = PLATFORM_ICONS[profile.platform] || FiGlobe;
        return (
          <a
            key={`${profile.platform}-${profile.url}`}
            href={withProtocol(profile.url)}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-600 transition-colors hover:border-primary-300 hover:bg-primary-50 hover:text-primary-700"
          >
            <Icon className="h-4 w-4" />
            {SOCIAL_PLATFORM_LABELS[profile.platform] || profile.platform}
          </a>
        );
      })}
    </div>
  );
}
