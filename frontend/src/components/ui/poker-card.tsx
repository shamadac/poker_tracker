"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

// Card suits and their symbols
const SUITS = {
  hearts: '♥',
  diamonds: '♦',
  clubs: '♣',
  spades: '♠'
} as const

// Card ranks
const RANKS = {
  '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7', '8': '8', '9': '9',
  'T': '10', 'J': 'J', 'Q': 'Q', 'K': 'K', 'A': 'A'
} as const

type Suit = keyof typeof SUITS
type Rank = keyof typeof RANKS

export interface PokerCardProps {
  rank?: Rank
  suit?: Suit
  faceDown?: boolean
  size?: 'sm' | 'md' | 'lg'
  className?: string
  animated?: boolean
  onClick?: () => void
}

const PokerCard = React.forwardRef<HTMLDivElement, PokerCardProps>(
  ({ rank, suit, faceDown = false, size = 'md', className, animated = true, onClick }, ref) => {
    const [isFlipping, setIsFlipping] = React.useState(false)
    const [showFront, setShowFront] = React.useState(!faceDown)

    const isRed = suit === 'hearts' || suit === 'diamonds'
    
    const sizeClasses = {
      sm: 'w-12 h-16 text-xs',
      md: 'w-16 h-24 text-sm',
      lg: 'w-20 h-32 text-base'
    }

    const handleClick = () => {
      if (onClick) {
        onClick()
      }
      
      if (faceDown && animated) {
        setIsFlipping(true)
        setTimeout(() => {
          setShowFront(true)
          setTimeout(() => setIsFlipping(false), 300)
        }, 150)
      }
    }

    const cardContent = showFront && rank && suit ? (
      <div className="flex flex-col justify-between h-full p-1">
        <div className={cn("font-bold leading-none", isRed ? "text-red-600" : "text-black")}>
          <div>{RANKS[rank]}</div>
          <div className="text-lg leading-none">{SUITS[suit]}</div>
        </div>
        <div className={cn("self-center text-2xl", isRed ? "text-red-600" : "text-black")}>
          {SUITS[suit]}
        </div>
        <div className={cn("font-bold leading-none rotate-180 self-end", isRed ? "text-red-600" : "text-black")}>
          <div>{RANKS[rank]}</div>
          <div className="text-lg leading-none">{SUITS[suit]}</div>
        </div>
      </div>
    ) : (
      <div className="flex items-center justify-center h-full">
        <div className="w-8 h-8 bg-blue-800 rounded-sm flex items-center justify-center">
          <div className="w-6 h-6 border-2 border-white rounded-sm bg-blue-900"></div>
        </div>
      </div>
    )

    return (
      <div
        ref={ref}
        className={cn(
          "relative cursor-pointer select-none transition-all duration-200",
          sizeClasses[size],
          animated && "hover:scale-105 hover:shadow-lg",
          isFlipping && "animate-pulse",
          className
        )}
        onClick={handleClick}
      >
        <div
          className={cn(
            "w-full h-full rounded-lg border-2 shadow-md transition-all duration-300",
            showFront && rank && suit
              ? "bg-white border-gray-300"
              : "bg-gradient-to-br from-blue-800 to-blue-900 border-blue-700",
            isFlipping && "scale-x-0"
          )}
          style={{
            transformStyle: 'preserve-3d',
            transform: isFlipping ? 'rotateY(90deg)' : 'rotateY(0deg)'
          }}
        >
          {cardContent}
        </div>
      </div>
    )
  }
)

PokerCard.displayName = "PokerCard"

// Helper component for displaying hole cards
export interface HoleCardsProps {
  cards: string[]
  size?: 'sm' | 'md' | 'lg'
  className?: string
  animated?: boolean
}

export const HoleCards = React.forwardRef<HTMLDivElement, HoleCardsProps>(
  ({ cards, size = 'md', className, animated = true }, ref) => {
    const parseCard = (cardStr: string): { rank: Rank; suit: Suit } | null => {
      if (cardStr.length !== 2) return null
      const rank = cardStr[0] as Rank
      const suitChar = cardStr[1].toLowerCase()
      const suit = suitChar === 'h' ? 'hearts' : 
                   suitChar === 'd' ? 'diamonds' :
                   suitChar === 'c' ? 'clubs' :
                   suitChar === 's' ? 'spades' : null
      
      if (!suit || !(rank in RANKS)) return null
      return { rank, suit }
    }

    return (
      <div ref={ref} className={cn("flex gap-1", className)}>
        {cards.slice(0, 2).map((cardStr, index) => {
          const parsed = parseCard(cardStr)
          return (
            <PokerCard
              key={index}
              rank={parsed?.rank}
              suit={parsed?.suit}
              size={size}
              animated={animated}
              faceDown={!parsed}
            />
          )
        })}
      </div>
    )
  }
)

HoleCards.displayName = "HoleCards"

// Helper component for displaying community cards
export interface CommunityCardsProps {
  cards: string[]
  size?: 'sm' | 'md' | 'lg'
  className?: string
  animated?: boolean
}

export const CommunityCards = React.forwardRef<HTMLDivElement, CommunityCardsProps>(
  ({ cards, size = 'md', className, animated = true }, ref) => {
    const parseCard = (cardStr: string): { rank: Rank; suit: Suit } | null => {
      if (cardStr.length !== 2) return null
      const rank = cardStr[0] as Rank
      const suitChar = cardStr[1].toLowerCase()
      const suit = suitChar === 'h' ? 'hearts' : 
                   suitChar === 'd' ? 'diamonds' :
                   suitChar === 'c' ? 'clubs' :
                   suitChar === 's' ? 'spades' : null
      
      if (!suit || !(rank in RANKS)) return null
      return { rank, suit }
    }

    // Show up to 5 community cards (flop, turn, river)
    const communityCards = Array.from({ length: 5 }, (_, index) => {
      const cardStr = cards[index]
      const parsed = cardStr ? parseCard(cardStr) : null
      return { parsed, revealed: !!cardStr }
    })

    return (
      <div ref={ref} className={cn("flex gap-1", className)}>
        {communityCards.map((card, index) => (
          <PokerCard
            key={index}
            rank={card.parsed?.rank}
            suit={card.parsed?.suit}
            size={size}
            animated={animated}
            faceDown={!card.revealed}
          />
        ))}
      </div>
    )
  }
)

CommunityCards.displayName = "CommunityCards"

export { PokerCard }